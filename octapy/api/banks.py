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
- Parts: 8 × 6331 bytes = 50648 bytes (4 unsaved + 4 saved)
- Part names: 4 × 7 bytes
- Checksum: 2 bytes (big-endian u16)

Ported from ot-tools-io (Rust).
"""

from enum import IntEnum
from pathlib import Path
from typing import Optional

from . import OTBlock, MachineType, read_u16_le, write_u16_le, read_u16_be, write_u16_be
from .patterns import PatternArray, Pattern, PATTERN_SIZE
from .parts import Parts, Part, PART_BLOCK_SIZE
from .projects import read_template_file


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
    PARTS = 0x8EED6                 # 8 parts start here (4 unsaved + 4 saved)
    FLEX_COUNTER = 0x9B4B2          # Counter for active flex slots
    CHECKSUM = 0x9B4CF              # 2-byte checksum (big-endian u16)


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

        # Patterns and Parts are initialized lazily when accessing
        self._patterns: Optional[PatternArray] = None
        self._parts: Optional[Parts] = None

    @classmethod
    def read(cls, data) -> "BankFile":
        """Read bank from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BANK_FILE_SIZE])
        instance._patterns = None
        instance._parts = None
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
        self.sync_patterns()

        # Sync any modified parts data back
        self.sync_parts()

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

    # === Parts ===

    @property
    def parts(self) -> Parts:
        """
        Get the parts container (lazy loaded).

        Parts contain machine types, slot assignments, and track parameters.
        Each bank has 4 parts, stored in both unsaved (working) and saved states.

        Usage:
            # Get Part 1's unsaved state (index 0)
            part = bank.parts.unsaved[0]

            # Set machine type on track 1
            part.set_machine_type(1, MachineType.FLEX)

            # Set flex slot on track 1
            part.set_flex_slot(1, slot=0)  # 0-indexed slot

        Returns:
            Parts container with unsaved[0-3] and saved[0-3] lists
        """
        if self._parts is None:
            self._parts = Parts.read(
                self._data,
                unsaved_offset=BankOffset.PARTS,
                saved_offset=BankOffset.PARTS + 4 * PART_BLOCK_SIZE,
                part_size=PART_BLOCK_SIZE,
            )
        return self._parts

    def get_part(self, part: int, saved: bool = False) -> Part:
        """
        Get a specific part.

        Args:
            part: Part number (1-4)
            saved: If True, get the saved state; otherwise get unsaved (working) state

        Returns:
            Part instance
        """
        parts_list = self.parts.saved if saved else self.parts.unsaved
        return parts_list[part - 1]

    def sync_parts(self):
        """Write any modified parts data back to the buffer."""
        if self._parts is not None:
            self._parts.write_to(
                self._data,
                unsaved_offset=BankOffset.PARTS,
                saved_offset=BankOffset.PARTS + 4 * PART_BLOCK_SIZE,
            )

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

        The checksum is a 16-bit value calculated as:
        template_checksum + sum_of_byte_differences (mod 65536)

        Where byte differences are calculated from offset 16 to end-2
        (skipping header and checksum bytes).
        """
        # Make sure patterns and parts are synced
        self.sync_patterns()
        self.sync_parts()

        # Load template for comparison
        template = read_template_file('bank01.work')
        template_checksum = read_u16_be(template, BankOffset.CHECKSUM)

        # Calculate byte differences from template (offset 16 to checksum)
        byte_diffs = 0
        for i in range(16, BankOffset.CHECKSUM):
            byte_diffs += self._data[i] - template[i]

        return (template_checksum + byte_diffs) & 0xFFFF

    def update_checksum(self):
        """Recalculate and update the checksum (2 bytes, big-endian)."""
        write_u16_be(self._data, BankOffset.CHECKSUM, self.calculate_checksum())

    def verify_checksum(self) -> bool:
        """Verify the checksum matches the calculated value."""
        stored = read_u16_be(self._data, BankOffset.CHECKSUM)
        return stored == self.calculate_checksum()

    # === Write helper ===

    def write(self) -> bytes:
        """Get the bank data as bytes (includes syncing patterns, parts, and checksum)."""
        self.sync_patterns()
        self.sync_parts()
        self.update_checksum()
        return bytes(self._data)
