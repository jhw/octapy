"""
Bank file I/O for Octatrack.

A bank file (bank01.work - bank16.work) contains:
- 16 patterns with trig data for 8 audio + 8 MIDI tracks
- 4 parts with track settings and parameters
- Part metadata (saved state, edited mask, names)

File layout (636113 bytes total):
- Header: 21 bytes ("FORM....DPS1BANK.....")
- Version: 1 byte (23)
- Patterns: 16 × 36588 bytes = 585408 bytes
- Parts: 8 × 6331 bytes = 50648 bytes (4 unsaved + 4 saved)
- Part names: 4 × 7 bytes
- Checksum: 2 bytes (big-endian u16)
"""

from enum import IntEnum
from pathlib import Path

from .base import OTBlock, read_u16_be, write_u16_be


# =============================================================================
# Constants
# =============================================================================

# Bank file
BANK_FILE_SIZE = 636113
BANK_HEADER = bytes([
    0x46, 0x4f, 0x52, 0x4d, 0x00, 0x00, 0x00, 0x00,
    0x44, 0x50, 0x53, 0x31, 0x42, 0x41, 0x4e, 0x4b,
    0x00, 0x00, 0x00, 0x00, 0x00
])  # "FORM....DPS1BANK....."
BANK_FILE_VERSION = 23

# Pattern and track sizes
PATTERN_SIZE = 0x8EEC           # 36588 bytes per pattern
AUDIO_TRACK_SIZE = 0x922        # 2338 bytes per audio track
MIDI_TRACK_SIZE = 0x4AC         # 1196 bytes per MIDI track

# Headers
PATTERN_HEADER = bytes([0x50, 0x54, 0x52, 0x4E, 0x00, 0x00, 0x00, 0x00])  # "PTRN...."
AUDIO_TRACK_HEADER = bytes([0x54, 0x52, 0x41, 0x43])  # "TRAC"
PART_HEADER = bytes([0x50, 0x41, 0x52, 0x54])  # "PART"

# Part block size
PART_BLOCK_SIZE = 6331

# Machine slot size
MACHINE_SLOT_SIZE = 5


# =============================================================================
# Offset Enums
# =============================================================================

class BankOffset(IntEnum):
    """Offsets within a bank file."""
    HEADER = 0                      # 21 bytes
    VERSION = 21                    # 1 byte
    PATTERNS = 22                   # 16 patterns start here (0x16)
    PARTS = 0x8EED6                 # 8 parts start here (4 unsaved + 4 saved)
    FLEX_COUNTER = 0x9B4B2          # Counter for active flex slots
    CHECKSUM = 0x9B4CF              # 2-byte checksum (big-endian u16)


class AudioTrackOffset(IntEnum):
    """Offsets within an audio track block (relative to track start)."""
    HEADER = 0                  # 4 bytes: "TRAC"
    UNKNOWN_1 = 4               # 4 bytes
    TRACK_ID = 8                # 1 byte: track number (0-7)
    TRIG_TRIGGER = 9            # 8 bytes: trigger trig masks
    TRIG_TRIGLESS = 17          # 8 bytes: trigless trig masks
    TRIG_PLOCK = 25             # 8 bytes: parameter lock trig masks
    TRIG_ONESHOT = 33           # 8 bytes: oneshot/hold trig masks
    TRIG_RECORDER = 41          # 32 bytes: recorder trig masks
    TRIG_SWING = 73             # 8 bytes: swing trig masks
    TRIG_SLIDE = 81             # 8 bytes: slide trig masks
    PER_TRACK_LEN = 89          # 1 byte: track length in per-track mode
    PER_TRACK_SCALE = 90        # 1 byte: track scale in per-track mode
    SWING_AMOUNT = 91           # 1 byte: swing amount (0-30)
    START_SILENT = 92           # 1 byte: start silent setting
    PLAYS_FREE = 93             # 1 byte: plays free setting
    TRIG_MODE = 94              # 1 byte: trig mode
    TRIG_QUANT = 95             # 1 byte: trig quantization
    ONESHOT_TRK = 96            # 1 byte: oneshot track setting


class PatternOffset(IntEnum):
    """Offsets within a pattern block (relative to pattern start)."""
    HEADER = 0                  # 8 bytes: "PTRN...."
    AUDIO_TRACKS = 8            # 8 audio tracks, each AUDIO_TRACK_SIZE bytes
    SCALE_LENGTH = 36577        # 1 byte: pattern length (16 = 16 steps)
    SCALE_MULT = 36578          # 1 byte: scale multiplier
    PART_ASSIGNMENT = 36581     # 1 byte: assigned part (0-3 = Part 1-4)


class PartOffset(IntEnum):
    """Byte offsets within a Part block."""
    HEADER = 0                      # 4 bytes: "PART"
    DATA_BLOCK_1 = 4                # 4 bytes: always 0
    PART_ID = 8                     # 1 byte: 0-3
    AUDIO_TRACK_FX1 = 9             # 8 bytes: FX1 type per track
    AUDIO_TRACK_FX2 = 17            # 8 bytes: FX2 type per track
    ACTIVE_SCENE_A = 25             # 1 byte: scene A (0-15)
    ACTIVE_SCENE_B = 26             # 1 byte: scene B (0-15)
    AUDIO_TRACK_VOLUMES = 27        # 16 bytes: main/cue volume per track
    AUDIO_TRACK_MACHINE_TYPES = 43  # 8 bytes: machine type per track
    AUDIO_TRACK_MACHINE_SLOTS = 723 # 40 bytes: 8 tracks * 5 bytes


class MachineSlotOffset(IntEnum):
    """Offsets within AudioTrackMachineSlot (5 bytes per track)."""
    STATIC_SLOT_ID = 0
    FLEX_SLOT_ID = 1
    UNUSED_1 = 2
    UNUSED_2 = 3
    RECORDER_SLOT_ID = 4


# =============================================================================
# BankFile Class
# =============================================================================

class BankFile(OTBlock):
    """
    Low-level Octatrack Bank file I/O.

    Provides raw buffer access for patterns and parts.
    Use offset enums to read/write specific fields.
    """

    BLOCK_SIZE = BANK_FILE_SIZE

    def __init__(self):
        super().__init__()
        self._data = bytearray(BANK_FILE_SIZE)
        self._data[0:21] = BANK_HEADER
        self._data[BankOffset.VERSION] = BANK_FILE_VERSION

    @classmethod
    def read(cls, data) -> "BankFile":
        """Read bank from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BANK_FILE_SIZE])
        return instance

    @classmethod
    def from_file(cls, path: Path) -> "BankFile":
        """Load a bank file from disk."""
        with open(path, 'rb') as f:
            data = f.read()
        return cls.read(data)

    def to_file(self, path: Path):
        """Write the bank file to disk."""
        self.update_checksum()
        with open(path, 'wb') as f:
            f.write(self._data)

    @classmethod
    def new(cls, bank_num: int = 1) -> "BankFile":
        """Create a new bank file from the embedded template."""
        from .project import read_template_file
        filename = f"bank{bank_num:02d}.work"
        data = read_template_file(filename)
        return cls.read(data)

    # === Header and version ===

    @property
    def header(self) -> bytes:
        return bytes(self._data[0:21])

    @property
    def version(self) -> int:
        return self._data[BankOffset.VERSION]

    def check_header(self) -> bool:
        return self.header == BANK_HEADER

    def check_version(self) -> bool:
        return self.version == BANK_FILE_VERSION

    # === Raw offset access ===

    def pattern_offset(self, pattern: int) -> int:
        """Get byte offset for pattern (1-16)."""
        return BankOffset.PATTERNS + (pattern - 1) * PATTERN_SIZE

    def audio_track_offset(self, pattern: int, track: int) -> int:
        """Get byte offset for audio track (pattern 1-16, track 1-8)."""
        pat_offset = self.pattern_offset(pattern)
        return pat_offset + PatternOffset.AUDIO_TRACKS + (track - 1) * AUDIO_TRACK_SIZE

    def part_offset(self, part: int, saved: bool = False) -> int:
        """Get byte offset for part (1-4)."""
        base = BankOffset.PARTS
        if saved:
            base += 4 * PART_BLOCK_SIZE
        return base + (part - 1) * PART_BLOCK_SIZE

    # === Flex counter ===

    @property
    def flex_count(self) -> int:
        return self._data[BankOffset.FLEX_COUNTER]

    @flex_count.setter
    def flex_count(self, value: int):
        self._data[BankOffset.FLEX_COUNTER] = value & 0xFF

    # === Trig helpers (for testing) ===

    def get_trigs(self, pattern: int, track: int) -> list:
        """Get trigger steps for a track in a pattern."""
        offset = self.audio_track_offset(pattern, track) + AudioTrackOffset.TRIG_TRIGGER
        return self._trig_mask_to_steps(offset)

    def set_trigs(self, pattern: int, track: int, steps: list):
        """Set trigger steps for a track in a pattern."""
        offset = self.audio_track_offset(pattern, track) + AudioTrackOffset.TRIG_TRIGGER
        self._steps_to_trig_mask(offset, steps)

    def _trig_mask_to_steps(self, offset: int) -> list:
        """Convert 8-byte trig mask to list of step numbers (1-64)."""
        steps = []
        data = self._data

        # Page 1 (bytes 6-7)
        for bit in range(8):
            if data[offset + 7] & (1 << bit):
                steps.append(bit + 1)
        for bit in range(8):
            if data[offset + 6] & (1 << bit):
                steps.append(bit + 9)

        # Page 2 (bytes 4-5)
        for bit in range(8):
            if data[offset + 4] & (1 << bit):
                steps.append(bit + 17)
        for bit in range(8):
            if data[offset + 5] & (1 << bit):
                steps.append(bit + 25)

        # Page 3 (bytes 2-3)
        for bit in range(8):
            if data[offset + 2] & (1 << bit):
                steps.append(bit + 33)
        for bit in range(8):
            if data[offset + 3] & (1 << bit):
                steps.append(bit + 41)

        # Page 4 (bytes 0-1)
        for bit in range(8):
            if data[offset + 0] & (1 << bit):
                steps.append(bit + 49)
        for bit in range(8):
            if data[offset + 1] & (1 << bit):
                steps.append(bit + 57)

        return sorted(steps)

    def _steps_to_trig_mask(self, offset: int, steps: list):
        """Convert list of step numbers (1-64) to 8-byte trig mask."""
        data = self._data

        # Clear existing mask
        for i in range(8):
            data[offset + i] = 0

        for step in steps:
            if step < 1 or step > 64:
                continue

            if step <= 8:
                data[offset + 7] |= (1 << (step - 1))
            elif step <= 16:
                data[offset + 6] |= (1 << (step - 9))
            elif step <= 24:
                data[offset + 4] |= (1 << (step - 17))
            elif step <= 32:
                data[offset + 5] |= (1 << (step - 25))
            elif step <= 40:
                data[offset + 2] |= (1 << (step - 33))
            elif step <= 48:
                data[offset + 3] |= (1 << (step - 41))
            elif step <= 56:
                data[offset + 0] |= (1 << (step - 49))
            else:
                data[offset + 1] |= (1 << (step - 57))

    # === Checksum ===

    def calculate_checksum(self) -> int:
        """Calculate checksum for bank file."""
        from .project import read_template_file
        template = read_template_file('bank01.work')
        template_checksum = read_u16_be(template, BankOffset.CHECKSUM)

        byte_diffs = 0
        for i in range(16, BankOffset.CHECKSUM):
            byte_diffs += self._data[i] - template[i]

        return (template_checksum + byte_diffs) & 0xFFFF

    def update_checksum(self):
        """Recalculate and update the checksum."""
        write_u16_be(self._data, BankOffset.CHECKSUM, self.calculate_checksum())

    def verify_checksum(self) -> bool:
        """Verify the checksum matches the calculated value."""
        stored = read_u16_be(self._data, BankOffset.CHECKSUM)
        return stored == self.calculate_checksum()
