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
    UNKNOWN_2 = 97              # 1 byte
    PLOCKS = 98                 # 64 × 32 bytes = 2048 bytes of p-lock data
    UNKNOWN_3 = 2146            # 64 bytes
    TRIG_CONDITIONS = 2210      # 64 × 2 bytes: micro timing + count + condition


# P-lock data structure (32 bytes per step)
PLOCK_SIZE = 32
NUM_STEPS = 64


class PlockOffset(IntEnum):
    """Offsets within a single step's p-lock data (32 bytes per step)."""
    # Machine/Playback page (6 bytes)
    MACHINE_PARAM1 = 0          # PTCH for Flex/Static
    MACHINE_PARAM2 = 1
    MACHINE_PARAM3 = 2
    MACHINE_PARAM4 = 3
    MACHINE_PARAM5 = 4
    MACHINE_PARAM6 = 5
    # LFO page (6 bytes)
    LFO_SPD1 = 6
    LFO_SPD2 = 7
    LFO_SPD3 = 8
    LFO_DEP1 = 9
    LFO_DEP2 = 10
    LFO_DEP3 = 11
    # AMP page (6 bytes)
    AMP_ATK = 12
    AMP_HOLD = 13
    AMP_REL = 14
    AMP_VOL = 15
    AMP_BAL = 16
    AMP_F = 17                  # <F> parameter for scenes/LFOs
    # FX1 page (6 bytes)
    FX1_PARAM1 = 18
    FX1_PARAM2 = 19
    FX1_PARAM3 = 20
    FX1_PARAM4 = 21
    FX1_PARAM5 = 22
    FX1_PARAM6 = 23
    # FX2 page (6 bytes)
    FX2_PARAM1 = 24
    FX2_PARAM2 = 25
    FX2_PARAM3 = 26
    FX2_PARAM4 = 27
    FX2_PARAM5 = 28
    FX2_PARAM6 = 29
    # Sample locks
    STATIC_SLOT_ID = 30
    FLEX_SLOT_ID = 31


# P-lock disabled value (255 = no p-lock set)
PLOCK_DISABLED = 255


class PatternOffset(IntEnum):
    """Offsets within a pattern block (relative to pattern start)."""
    HEADER = 0                  # 8 bytes: "PTRN...."
    AUDIO_TRACKS = 8            # 8 audio tracks, each AUDIO_TRACK_SIZE bytes
    MIDI_TRACKS = 18712         # 8 MIDI tracks start here (0x4918)
    SCALE_LENGTH = 36577        # 1 byte: pattern length (16 = 16 steps)
    SCALE_MULT = 36578          # 1 byte: scale multiplier
    PART_ASSIGNMENT = 36581     # 1 byte: assigned part (0-3 = Part 1-4)


# MIDI track pattern size (MidiTrackTrigs structure)
MIDI_TRACK_PATTERN_SIZE = 2233  # bytes per MIDI track in pattern


class MidiTrackTrigsOffset(IntEnum):
    """Offsets within MidiTrackTrigs (2233 bytes per track).

    Structure:
    - header (4 bytes): "MTRA"
    - unknown_1 (4 bytes)
    - track_id (1 byte)
    - trig_masks (40 bytes): trigger, trigless, plock, swing, unknown
    - scale_per_track_mode (2 bytes)
    - swing_amount (1 byte)
    - pattern_settings (5 bytes)
    - plocks (2048 bytes): 64 steps * 32 bytes
    - trig_conditions (128 bytes): 64 steps * 2 bytes
    """
    HEADER = 0              # 4 bytes: "MTRA"
    UNKNOWN_1 = 4           # 4 bytes
    TRACK_ID = 8            # 1 byte
    TRIG_TRIGGER = 9        # 8 bytes: trigger trig masks
    TRIG_TRIGLESS = 17      # 8 bytes: trigless trig masks
    TRIG_PLOCK = 25         # 8 bytes: p-lock trig masks
    TRIG_SWING = 33         # 8 bytes: swing trig masks
    TRIG_UNKNOWN = 41       # 8 bytes: unknown masks
    PER_TRACK_LEN = 49      # 1 byte
    PER_TRACK_SCALE = 50    # 1 byte
    SWING_AMOUNT = 51       # 1 byte
    PATTERN_SETTINGS = 52   # 5 bytes: start_silent, plays_free, trig_mode, trig_quant, oneshot_trk
    PLOCKS = 57             # 2048 bytes: 64 steps * 32 bytes
    TRIG_CONDITIONS = 2105  # 128 bytes: 64 steps * 2 bytes


# MIDI p-lock size per step
MIDI_PLOCK_SIZE = 32


class MidiPlockOffset(IntEnum):
    """Offsets within MidiTrackParameterLocks (32 bytes per step).

    Structure:
    - midi (6 bytes): note, vel, len, not2, not3, not4
    - lfo (6 bytes): spd1, spd2, spd3, dep1, dep2, dep3
    - arp (6 bytes): tran, leg, mode, spd, rnge, nlen
    - ctrl1 (6 bytes): pb, at, cc1, cc2, cc3, cc4
    - ctrl2 (6 bytes): cc5, cc6, cc7, cc8, cc9, cc10
    - unknown (2 bytes)
    """
    # MIDI/Note page (offset 0-5)
    NOTE = 0
    VELOCITY = 1
    LENGTH = 2
    NOTE2 = 3
    NOTE3 = 4
    NOTE4 = 5
    # LFO page (offset 6-11)
    LFO_SPD1 = 6
    LFO_SPD2 = 7
    LFO_SPD3 = 8
    LFO_DEP1 = 9
    LFO_DEP2 = 10
    LFO_DEP3 = 11
    # Arp page (offset 12-17)
    ARP_TRAN = 12
    ARP_LEG = 13
    ARP_MODE = 14
    ARP_SPD = 15
    ARP_RNGE = 16
    ARP_NLEN = 17
    # CC1 page (offset 18-23)
    PITCH_BEND = 18
    AFTERTOUCH = 19
    CC1 = 20
    CC2 = 21
    CC3 = 22
    CC4 = 23
    # CC2 page (offset 24-29)
    CC5 = 24
    CC6 = 25
    CC7 = 26
    CC8 = 27
    CC9 = 28
    CC10 = 29


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
    # Machine params values (Playback page): 8 tracks * 30 bytes = 240 bytes
    AUDIO_TRACK_MACHINE_PARAMS_VALUES = 51
    # Track params values (LFO/Amp/FX): 8 tracks * 24 bytes = 192 bytes
    AUDIO_TRACK_PARAMS_VALUES = 291
    # Machine params setup: 8 tracks * 30 bytes = 240 bytes
    AUDIO_TRACK_MACHINE_PARAMS_SETUP = 483
    AUDIO_TRACK_MACHINE_SLOTS = 723 # 40 bytes: 8 tracks * 5 bytes


# Machine params sizes
MACHINE_PARAMS_SIZE = 30  # 5 machines * 6 bytes per track


class MachineParamsOffset(IntEnum):
    """Offsets within AudioTrackMachinesParams (30 bytes per track).

    Each machine has 6 parameter bytes for the Playback page (Values)
    and 6 bytes for the Setup page.
    """
    STATIC = 0   # 6 bytes
    FLEX = 6     # 6 bytes
    THRU = 12    # 6 bytes
    NEIGHBOR = 18  # 6 bytes
    PICKUP = 24  # 6 bytes


class FlexStaticParamsOffset(IntEnum):
    """Playback page params for Flex/Static machines (6 bytes)."""
    PTCH = 0  # Pitch (64 = no transpose)
    STRT = 1  # Start point
    LEN = 2   # Length
    RATE = 3  # Playback rate
    RTRG = 4  # Retrig
    RTIM = 5  # Retrig time


class FlexStaticSetupOffset(IntEnum):
    """Setup page params for Flex/Static machines (6 bytes)."""
    LOOP = 0  # Loop mode
    SLIC = 1  # Slice mode
    LEN = 2   # Length mode
    RATE = 3  # Rate mode
    TSTR = 4  # Timestretch
    TSNS = 5  # Timestretch sensitivity


class ThruParamsOffset(IntEnum):
    """Playback page params for Thru machine (6 bytes)."""
    IN_AB = 0    # Input A/B select
    VOL_AB = 1   # Volume A/B
    UNUSED_1 = 2
    IN_CD = 3    # Input C/D select
    VOL_CD = 4   # Volume C/D
    UNUSED_2 = 5


class PickupParamsOffset(IntEnum):
    """Playback page params for Pickup machine (6 bytes)."""
    PTCH = 0   # Pitch
    DIR = 1    # Direction
    LEN = 2    # Length
    UNUSED = 3
    GAIN = 4   # Gain
    OP = 5     # Operation mode


class PickupSetupOffset(IntEnum):
    """Setup page params for Pickup machine (6 bytes)."""
    UNUSED_1 = 0
    UNUSED_2 = 1
    UNUSED_3 = 2
    UNUSED_4 = 3
    TSTR = 4   # Timestretch
    TSNS = 5   # Timestretch sensitivity


class MachineSlotOffset(IntEnum):
    """Offsets within AudioTrackMachineSlot (5 bytes per track)."""
    STATIC_SLOT_ID = 0
    FLEX_SLOT_ID = 1
    UNUSED_1 = 2
    UNUSED_2 = 3
    RECORDER_SLOT_ID = 4


# Audio track params size (LFO + AMP + FX1 + FX2 = 24 bytes)
AUDIO_TRACK_PARAMS_SIZE = 24


class AudioTrackParamsOffset(IntEnum):
    """Offsets within AudioTrackParamsValues (24 bytes per track).

    Contains default values for LFO, AMP, FX1, and FX2 pages.
    These are shared across all machine types.
    """
    # LFO page (6 bytes)
    LFO_SPD1 = 0
    LFO_SPD2 = 1
    LFO_SPD3 = 2
    LFO_DEP1 = 3
    LFO_DEP2 = 4
    LFO_DEP3 = 5
    # AMP page (6 bytes)
    AMP_ATK = 6
    AMP_HOLD = 7
    AMP_REL = 8
    AMP_VOL = 9
    AMP_BAL = 10
    AMP_UNUSED = 11
    # FX1 page (6 bytes)
    FX1_PARAM1 = 12
    FX1_PARAM2 = 13
    FX1_PARAM3 = 14
    FX1_PARAM4 = 15
    FX1_PARAM5 = 16
    FX1_PARAM6 = 17
    # FX2 page (6 bytes)
    FX2_PARAM1 = 18
    FX2_PARAM2 = 19
    FX2_PARAM3 = 20
    FX2_PARAM4 = 21
    FX2_PARAM5 = 22
    FX2_PARAM6 = 23


# MIDI track data sizes
MIDI_TRACK_VALUES_SIZE = 32     # MidiTrackParamsValues: 32 bytes per track
MIDI_TRACK_SETUP_SIZE = 36      # MidiTrackParamsSetup: 36 bytes per track


class MidiPartOffset(IntEnum):
    """Byte offsets for MIDI track data within a Part block."""
    # MIDI track params values array (8 tracks * 32 bytes = 256 bytes)
    MIDI_TRACK_PARAMS_VALUES = 1003  # 0x3EB
    # MIDI track params setup array (8 tracks * 36 bytes = 288 bytes)
    MIDI_TRACK_PARAMS_SETUP = 1259   # 0x4EB


# =============================================================================
# Scene Data Offsets
# =============================================================================

# Scene data sizes
SCENE_PARAMS_SIZE = 32          # SceneParams: 32 bytes per track per scene
SCENE_TRACK_COUNT = 8           # 8 audio tracks per scene
SCENE_SIZE = 256                # SceneParamsArray: 8 tracks * 32 bytes
SCENE_COUNT = 16                # 16 scenes per part
SCENE_XLV_SIZE = 10             # SceneXlvAssignments: 8 tracks + 2 unknown


class SceneOffset(IntEnum):
    """Byte offsets for scene data within a Part block."""
    # Recorder setup: 8 tracks * 12 bytes = 96 bytes
    RECORDER_SETUP = 1547
    # Scene params: 16 scenes * 8 tracks * 32 bytes = 4096 bytes
    SCENES = 1643
    # Scene XLV (crossfader volume) assignments: 16 scenes * 10 bytes = 160 bytes
    SCENE_XLVS = 5739


class SceneParamsOffset(IntEnum):
    """Offsets within SceneParams (32 bytes per track per scene).

    Values of 255 indicate "no lock" (use Part default, don't morph).
    Any other value is the scene's lock destination.
    """
    # Machine/Playback page (6 bytes) - machine-specific params
    PLAYBACK_PARAM1 = 0
    PLAYBACK_PARAM2 = 1
    PLAYBACK_PARAM3 = 2
    PLAYBACK_PARAM4 = 3
    PLAYBACK_PARAM5 = 4
    PLAYBACK_PARAM6 = 5
    # LFO page (6 bytes)
    LFO_SPD1 = 6
    LFO_SPD2 = 7
    LFO_SPD3 = 8
    LFO_DEP1 = 9
    LFO_DEP2 = 10
    LFO_DEP3 = 11
    # AMP page (6 bytes)
    AMP_ATK = 12
    AMP_HOLD = 13
    AMP_REL = 14
    AMP_VOL = 15
    AMP_BAL = 16
    AMP_F = 17
    # FX1 page (6 bytes)
    FX1_PARAM1 = 18
    FX1_PARAM2 = 19
    FX1_PARAM3 = 20
    FX1_PARAM4 = 21
    FX1_PARAM5 = 22
    FX1_PARAM6 = 23
    # FX2 page (6 bytes)
    FX2_PARAM1 = 24
    FX2_PARAM2 = 25
    FX2_PARAM3 = 26
    FX2_PARAM4 = 27
    FX2_PARAM5 = 28
    FX2_PARAM6 = 29
    # Unknown/reserved (2 bytes)
    UNKNOWN_1 = 30
    UNKNOWN_2 = 31


# Scene lock disabled value (255 = no lock, use Part default)
SCENE_LOCK_DISABLED = 255


class MidiTrackValuesOffset(IntEnum):
    """Offsets within MidiTrackParamsValues (32 bytes per track).

    Structure:
    - midi (6 bytes): note, vel, len, not2, not3, not4
    - lfo (6 bytes): spd1, spd2, spd3, dep1, dep2, dep3
    - arp (6 bytes): tran, leg, mode, spd, rnge, nlen
    - ctrl1 (6 bytes): pb, at, cc1, cc2, cc3, cc4
    - ctrl2 (6 bytes): cc5, cc6, cc7, cc8, cc9, cc10
    - unknown (2 bytes)
    """
    # MIDI/Note page (offset 0-5)
    NOTE = 0
    VELOCITY = 1
    LENGTH = 2
    NOTE2 = 3
    NOTE3 = 4
    NOTE4 = 5
    # LFO page (offset 6-11)
    LFO_SPD1 = 6
    LFO_SPD2 = 7
    LFO_SPD3 = 8
    LFO_DEP1 = 9
    LFO_DEP2 = 10
    LFO_DEP3 = 11
    # Arp page (offset 12-17)
    ARP_TRAN = 12
    ARP_LEG = 13
    ARP_MODE = 14
    ARP_SPD = 15
    ARP_RNGE = 16
    ARP_NLEN = 17
    # CC1 page (offset 18-23)
    PITCH_BEND = 18
    AFTERTOUCH = 19
    CC1_VALUE = 20
    CC2_VALUE = 21
    CC3_VALUE = 22
    CC4_VALUE = 23
    # CC2 page (offset 24-29)
    CC5_VALUE = 24
    CC6_VALUE = 25
    CC7_VALUE = 26
    CC8_VALUE = 27
    CC9_VALUE = 28
    CC10_VALUE = 29


class MidiTrackSetupOffset(IntEnum):
    """Offsets within MidiTrackParamsSetup (36 bytes per track).

    Structure:
    - note (6 bytes): chan, bank, prog, unused_1, sbank, unused_2
    - lfo1 (6 bytes): lfo1_pmtr, lfo2_pmtr, lfo3_pmtr, lfo1_wave, lfo2_wave, lfo3_wave
    - arp (6 bytes): unused_1, unused_2, len, unused_3, unused_4, key
    - ctrl1 (6 bytes): unused_1, unused_2, cc1, cc2, cc3, cc4
    - ctrl2 (6 bytes): cc5, cc6, cc7, cc8, cc9, cc10
    - lfo2 (6 bytes): lfo1_mult, lfo2_mult, lfo3_mult, lfo1_trig, lfo2_trig, lfo3_trig
    """
    # Note setup page (offset 0-5)
    CHANNEL = 0
    BANK = 1
    PROGRAM = 2
    # offset 3 unused
    SBANK = 4
    # offset 5 unused
    # LFO setup 1 (offset 6-11)
    LFO1_PMTR = 6
    LFO2_PMTR = 7
    LFO3_PMTR = 8
    LFO1_WAVE = 9
    LFO2_WAVE = 10
    LFO3_WAVE = 11
    # Arp setup (offset 12-17)
    ARP_LEN = 14
    ARP_KEY = 17
    # CC1 setup (offset 18-23)
    CC1_NUMBER = 20
    CC2_NUMBER = 21
    CC3_NUMBER = 22
    CC4_NUMBER = 23
    # CC2 setup (offset 24-29)
    CC5_NUMBER = 24
    CC6_NUMBER = 25
    CC7_NUMBER = 26
    CC8_NUMBER = 27
    CC9_NUMBER = 28
    CC10_NUMBER = 29
    # LFO setup 2 (offset 30-35)
    LFO1_MULT = 30
    LFO2_MULT = 31
    LFO3_MULT = 32
    LFO1_TRIG = 33
    LFO2_TRIG = 34
    LFO3_TRIG = 35


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
