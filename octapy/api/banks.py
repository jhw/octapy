"""
Bank file types and I/O for Octatrack.

A bank file (bank01.work - bank16.work) contains:
- 16 patterns with trig data for 8 audio + 8 MIDI tracks
- 4 parts with track settings and parameters
- Part metadata (saved state, edited mask, names)

File layout (636113 bytes total):
- Header: 21 bytes ("FORM....DPS1BANK.....")
- Version: 1 byte (23)
- Patterns: 16 × 36588 bytes = 585408 bytes
- Parts (unsaved + saved): variable
- Part names: 4 × 7 bytes
- Checksum: 1 byte

Ported from ot-tools-io (Rust).
"""

from enum import IntEnum
from pathlib import Path
from typing import Optional

from . import OTBlock, MachineType, read_u16_le, write_u16_le
from .patterns import PatternArray, Pattern, PATTERN_SIZE
from .parts import Parts, Part, PART_BLOCK_SIZE


# Bank file constants
BANK_FILE_SIZE = 636113
BANK_HEADER = bytes([
    0x46, 0x4f, 0x52, 0x4d, 0x00, 0x00, 0x00, 0x00,
    0x44, 0x50, 0x53, 0x31, 0x42, 0x41, 0x4e, 0x4b,
    0x00, 0x00, 0x00, 0x00, 0x00
])  # "FORM....DPS1BANK....."
BANK_FILE_VERSION = 23


class BankOffset(IntEnum):
    """Offsets within a bank file."""
    HEADER = 0                      # 21 bytes
    VERSION = 21                    # 1 byte
    PATTERNS = 22                   # 16 patterns start here (0x16)
    # After patterns: 16 * 0x8EEC = 0x8EEC0 bytes
    # Parts start at 0x8EEC0 + 0x16 = 0x8EED6
    MACHINE_TYPES_BASE = 0x8EF00    # Machine types at 0x8EF01-0x8EF08
    # Machine slots are 680 bytes after machine types (offset 723 - 43 in Part)
    MACHINE_SLOTS_BASE = 0x8F1A8    # Slot assignments: 8 tracks * 5 bytes each
    FLEX_COUNTER = 0x9B4B2          # Counter for active flex slots
    CHECKSUM = 0x9B4D0              # Last byte (checksum)


# Machine slot structure (5 bytes per track)
SLOT_SIZE = 5
SLOT_STATIC_ID = 0
SLOT_FLEX_ID = 1
SLOT_RECORDER_ID = 4


class BankFile(OTBlock):
    """
    An Octatrack Bank file containing patterns and parts.

    The bank file is a binary format with patterns, parts, and metadata.
    Uses pym8-style buffer-based access with typed helpers.
    """

    BLOCK_SIZE = BANK_FILE_SIZE

    def __init__(self):
        super().__init__()
        self._data = bytearray(BANK_FILE_SIZE)

        # Initialize header and version
        self._data[0:21] = BANK_HEADER
        self._data[BankOffset.VERSION] = BANK_FILE_VERSION

        # Patterns are initialized lazily when accessing
        self._patterns: Optional[PatternArray] = None

    @classmethod
    def read(cls, data) -> "BankFile":
        """Read bank from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BANK_FILE_SIZE])
        instance._patterns = None
        return instance

    @classmethod
    def from_file(cls, path: Path) -> "BankFile":
        """Load a bank file from disk."""
        with open(path, 'rb') as f:
            data = f.read()
        return cls.read(data)

    def to_file(self, path: Path):
        """Write the bank file to disk."""
        # Sync any modified pattern data back
        if self._patterns is not None:
            self._patterns.write_to(self._data, BankOffset.PATTERNS)

        # Update checksum
        self.update_checksum()

        with open(path, 'wb') as f:
            f.write(self._data)

    @classmethod
    def new(cls, bank_num: int = 1) -> "BankFile":
        """
        Create a new bank file from the embedded template.

        Args:
            bank_num: Bank number (1-16), used to select template file

        Returns:
            New BankFile instance with default values
        """
        from .projects import read_template_file
        filename = f"bank{bank_num:02d}.work"
        data = read_template_file(filename)
        return cls.read(data)

    # === Header and version ===

    @property
    def header(self) -> bytes:
        """Get the file header."""
        return bytes(self._data[0:21])

    @property
    def version(self) -> int:
        """Get the file version."""
        return self._data[BankOffset.VERSION]

    def check_header(self) -> bool:
        """Verify the header matches expected bank file header."""
        return self.header == BANK_HEADER

    def check_version(self) -> bool:
        """Verify the file version is supported."""
        return self.version == BANK_FILE_VERSION

    # === Patterns ===

    @property
    def patterns(self) -> PatternArray:
        """Get the patterns array (lazy loaded)."""
        if self._patterns is None:
            self._patterns = PatternArray.read(self._data, BankOffset.PATTERNS)
        return self._patterns

    def get_pattern(self, pattern: int) -> Pattern:
        """
        Get a specific pattern.

        Args:
            pattern: Pattern number (1-16)

        Returns:
            Pattern instance
        """
        return self.patterns[pattern - 1]

    def sync_patterns(self):
        """Write any modified pattern data back to the buffer."""
        if self._patterns is not None:
            self._patterns.write_to(self._data, BankOffset.PATTERNS)

    # === Machine types (stored in Part 1 unsaved) ===

    def get_machine_type(self, track: int) -> MachineType:
        """
        Get the machine type for an audio track.

        Args:
            track: Track number (1-8)

        Returns:
            MachineType enum value
        """
        offset = BankOffset.MACHINE_TYPES_BASE + track
        return MachineType(self._data[offset])

    def set_machine_type(self, track: int, machine_type: MachineType):
        """
        Set the machine type for an audio track.

        Note: This sets the machine type in the Part 1 unsaved state.

        Args:
            track: Track number (1-8)
            machine_type: MachineType enum value
        """
        offset = BankOffset.MACHINE_TYPES_BASE + track
        self._data[offset] = machine_type

    # === Slot assignments (stored in Part 1 unsaved) ===

    def get_flex_slot(self, track: int) -> int:
        """
        Get the flex sample slot assigned to a track.

        Args:
            track: Track number (1-8)

        Returns:
            Slot number (0-indexed, 0-127 for samples, 128-135 for recorders)
        """
        offset = BankOffset.MACHINE_SLOTS_BASE + (track - 1) * SLOT_SIZE + SLOT_FLEX_ID
        return self._data[offset]

    def set_flex_slot(self, track: int, slot: int):
        """
        Set the flex sample slot for a track.

        Args:
            track: Track number (1-8)
            slot: Slot number (0-indexed, 0-127 for samples, 128-135 for recorders)
        """
        offset = BankOffset.MACHINE_SLOTS_BASE + (track - 1) * SLOT_SIZE + SLOT_FLEX_ID
        self._data[offset] = slot & 0xFF

    def get_static_slot(self, track: int) -> int:
        """
        Get the static sample slot assigned to a track.

        Args:
            track: Track number (1-8)

        Returns:
            Slot number (0-indexed, 0-127)
        """
        offset = BankOffset.MACHINE_SLOTS_BASE + (track - 1) * SLOT_SIZE + SLOT_STATIC_ID
        return self._data[offset]

    def set_static_slot(self, track: int, slot: int):
        """
        Set the static sample slot for a track.

        Args:
            track: Track number (1-8)
            slot: Slot number (0-indexed, 0-127)
        """
        offset = BankOffset.MACHINE_SLOTS_BASE + (track - 1) * SLOT_SIZE + SLOT_STATIC_ID
        self._data[offset] = slot & 0xFF

    # === Flex counter ===

    @property
    def flex_count(self) -> int:
        """Get the flex slot counter (number of active flex sample slots)."""
        return self._data[BankOffset.FLEX_COUNTER]

    @flex_count.setter
    def flex_count(self, value: int):
        """Set the flex slot counter."""
        self._data[BankOffset.FLEX_COUNTER] = value & 0xFF

    # === Trigger helpers (convenience methods) ===

    def set_trigs(self, pattern: int, track: int, steps: list):
        """
        Set trigger steps for a track in a pattern.

        Args:
            pattern: Pattern number (1-16)
            track: Track number (1-8)
            steps: List of step numbers (1-64) that should have triggers
        """
        pat = self.get_pattern(pattern)
        pat.set_trigger_steps(track, steps)

    def get_trigs(self, pattern: int, track: int) -> list:
        """
        Get trigger steps for a track in a pattern.

        Args:
            pattern: Pattern number (1-16)
            track: Track number (1-8)

        Returns:
            List of step numbers (1-64) that have triggers
        """
        return self.get_pattern(pattern).get_trigger_steps(track)

    # === Checksum ===

    def calculate_checksum(self) -> int:
        """
        Calculate checksum for bank file.

        The checksum is (sum of all bytes except last byte - 1) mod 256.
        """
        # Make sure patterns are synced
        self.sync_patterns()

        total = sum(self._data[:-1])
        return (total - 1) & 0xFF

    def update_checksum(self):
        """Recalculate and update the checksum."""
        self._data[BankOffset.CHECKSUM] = self.calculate_checksum()

    def verify_checksum(self) -> bool:
        """Verify the checksum matches the calculated value."""
        return self._data[BankOffset.CHECKSUM] == self.calculate_checksum()

    # === Write helper ===

    def write(self) -> bytes:
        """Get the bank data as bytes (includes syncing patterns and checksum)."""
        self.sync_patterns()
        self.update_checksum()
        return bytes(self._data)
