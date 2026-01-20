"""
Bank - standalone Bank container with Parts and Patterns.

This is a standalone object that owns its data buffer and can be created
with constructor arguments or read from a bank file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..._io import (
    BankFile,
    BankOffset,
    PatternOffset,
    BANK_FILE_SIZE,
    PATTERN_SIZE,
    PART_BLOCK_SIZE,
)
from .part import Part
from .pattern import Pattern


class Bank:
    """
    Bank containing 4 Parts and 16 Patterns.

    This is a standalone object that owns its 636113-byte data buffer.

    A Bank contains:
    - 4 Part objects (machine configurations, scenes)
    - 16 Pattern objects (step sequences)
    - Flex slot counter

    Usage:
        # Create with constructor arguments
        bank = Bank(bank_num=1)
        bank.part(1).audio_track(1).machine_type = MachineType.FLEX
        bank.pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]

        # Read from file
        bank = Bank.from_file("bank01.work")

        # Write to file
        bank.to_file("bank01.work")

        # Create from template with octapy defaults
        bank = Bank.from_template(bank_num=1)
    """

    def __init__(
        self,
        bank_num: int = 1,
        flex_count: int = 0,
        parts: Optional[List[Part]] = None,
        patterns: Optional[List[Pattern]] = None,
    ):
        """
        Create a Bank with optional configurations.

        Args:
            bank_num: Bank number (1-16)
            flex_count: Number of active flex slots (0-127)
            parts: Optional list of 4 Part objects
            patterns: Optional list of 16 Pattern objects
        """
        self._bank_num = bank_num
        self._bank_file = BankFile()
        self._bank_file.flex_count = flex_count

        # Initialize collections
        self._parts: Dict[int, Part] = {}
        self._patterns: Dict[int, Pattern] = {}

        # Create default parts
        for i in range(1, 5):
            self._parts[i] = Part(part_num=i)

        # Create default patterns
        for i in range(1, 17):
            self._patterns[i] = Pattern(pattern_num=i)

        # Apply provided parts/patterns
        if parts:
            for part in parts:
                self._parts[part.part_num] = part

        if patterns:
            for pattern in patterns:
                self._patterns[pattern.pattern_num] = pattern

    @classmethod
    def from_template(cls, bank_num: int = 1) -> "Bank":
        """
        Create a Bank from the embedded template with octapy defaults.

        Applies octapy default overrides for better workflows:
        - SRC page: loop_mode=OFF, length_mode=TIME, length=127
        - Recorder: RLEN=16, QREC=PLEN, all sources OFF

        Args:
            bank_num: Bank number (1-16)

        Returns:
            Bank instance with octapy defaults
        """
        instance = cls.__new__(cls)
        instance._bank_num = bank_num
        instance._bank_file = BankFile.new(bank_num)
        instance._parts = {}
        instance._patterns = {}

        # Load parts from template data
        for i in range(1, 5):
            part_offset = instance._bank_file.part_offset(i)
            instance._parts[i] = Part.read_from_bank(i, instance._bank_file._data, part_offset)

        # Load patterns from template data
        for i in range(1, 17):
            pattern_offset = instance._bank_file.pattern_offset(i)
            instance._patterns[i] = Pattern.read_from_bank(i, instance._bank_file._data, pattern_offset)

        return instance

    @classmethod
    def from_file(cls, path: Path | str) -> "Bank":
        """
        Read a Bank from a bank file.

        Args:
            path: Path to bank file (e.g., "bank01.work")

        Returns:
            Bank instance
        """
        path = Path(path)
        instance = cls.__new__(cls)
        instance._bank_num = cls._parse_bank_num(path)
        instance._bank_file = BankFile.from_file(path)
        instance._parts = {}
        instance._patterns = {}

        # Load parts
        for i in range(1, 5):
            part_offset = instance._bank_file.part_offset(i)
            instance._parts[i] = Part.read_from_bank(i, instance._bank_file._data, part_offset)

        # Load patterns
        for i in range(1, 17):
            pattern_offset = instance._bank_file.pattern_offset(i)
            instance._patterns[i] = Pattern.read_from_bank(i, instance._bank_file._data, pattern_offset)

        return instance

    @classmethod
    def read(cls, bank_num: int, data: bytes) -> "Bank":
        """
        Read a Bank from binary data.

        Args:
            bank_num: Bank number (1-16)
            data: Bank binary data (636113 bytes)

        Returns:
            Bank instance
        """
        instance = cls.__new__(cls)
        instance._bank_num = bank_num
        instance._bank_file = BankFile.read(data)
        instance._parts = {}
        instance._patterns = {}

        # Load parts
        for i in range(1, 5):
            part_offset = instance._bank_file.part_offset(i)
            instance._parts[i] = Part.read_from_bank(i, instance._bank_file._data, part_offset)

        # Load patterns
        for i in range(1, 17):
            pattern_offset = instance._bank_file.pattern_offset(i)
            instance._patterns[i] = Pattern.read_from_bank(i, instance._bank_file._data, pattern_offset)

        return instance

    @staticmethod
    def _parse_bank_num(path: Path) -> int:
        """Parse bank number from filename (e.g., bank01.work -> 1)."""
        name = path.stem.lower()
        if name.startswith("bank") and len(name) >= 6:
            try:
                return int(name[4:6])
            except ValueError:
                pass
        return 1

    def to_file(self, path: Path | str):
        """
        Write this Bank to a bank file.

        Args:
            path: Path to write (e.g., "bank01.work")
        """
        self._sync_to_buffer()
        self._bank_file.to_file(Path(path))

    def write(self) -> bytes:
        """
        Write this Bank to binary data.

        Syncs all parts and patterns to the buffer before returning.

        Returns:
            636113 bytes of bank data
        """
        self._sync_to_buffer()
        return bytes(self._bank_file._data)

    def _sync_to_buffer(self):
        """Sync all parts and patterns back to the bank buffer."""
        # Sync parts
        for i in range(1, 5):
            part_offset = self._bank_file.part_offset(i)
            self._parts[i].write_to_bank(self._bank_file._data, part_offset)

        # Sync patterns
        for i in range(1, 17):
            pattern_offset = self._bank_file.pattern_offset(i)
            self._patterns[i].write_to_bank(self._bank_file._data, pattern_offset)

        # Update checksum
        self._bank_file.update_checksum()

    def clone(self) -> "Bank":
        """Create a copy of this Bank with all parts and patterns cloned."""
        instance = Bank.__new__(Bank)
        instance._bank_num = self._bank_num

        # Clone the bank file buffer
        self._sync_to_buffer()
        instance._bank_file = BankFile.read(bytes(self._bank_file._data))

        # Clone parts
        instance._parts = {}
        for i, part in self._parts.items():
            instance._parts[i] = part.clone()

        # Clone patterns
        instance._patterns = {}
        for i, pattern in self._patterns.items():
            instance._patterns[i] = pattern.clone()

        return instance

    # === Basic properties ===

    @property
    def bank_num(self) -> int:
        """Get the bank number (1-16)."""
        return self._bank_num

    @property
    def flex_count(self) -> int:
        """Get/set the flex slot counter."""
        return self._bank_file.flex_count

    @flex_count.setter
    def flex_count(self, value: int):
        self._bank_file.flex_count = value

    # === Part access ===

    def part(self, part_num: int) -> Part:
        """
        Get a Part (1-4).

        Args:
            part_num: Part number (1-4)

        Returns:
            Part instance
        """
        if part_num < 1 or part_num > 4:
            raise ValueError(f"Part number must be 1-4, got {part_num}")
        return self._parts[part_num]

    def set_part(self, part_num: int, part: Part):
        """
        Set a Part at the given position.

        Args:
            part_num: Part number (1-4)
            part: Part to set
        """
        if part_num < 1 or part_num > 4:
            raise ValueError(f"Part number must be 1-4, got {part_num}")
        part._part_num = part_num
        self._parts[part_num] = part

    # === Pattern access ===

    def pattern(self, pattern_num: int) -> Pattern:
        """
        Get a Pattern (1-16).

        Args:
            pattern_num: Pattern number (1-16)

        Returns:
            Pattern instance
        """
        if pattern_num < 1 or pattern_num > 16:
            raise ValueError(f"Pattern number must be 1-16, got {pattern_num}")
        return self._patterns[pattern_num]

    def set_pattern(self, pattern_num: int, pattern: Pattern):
        """
        Set a Pattern at the given position.

        Args:
            pattern_num: Pattern number (1-16)
            pattern: Pattern to set
        """
        if pattern_num < 1 or pattern_num > 16:
            raise ValueError(f"Pattern number must be 1-16, got {pattern_num}")
        pattern._pattern_num = pattern_num
        self._patterns[pattern_num] = pattern

    # === Serialization ===

    def to_dict(self, include_steps: bool = False, include_scenes: bool = False) -> dict:
        """
        Convert bank to dictionary.

        Args:
            include_steps: Include step data in patterns (default False)
            include_scenes: Include scene locks in parts (default False)

        Returns:
            Dict with bank number, flex count, parts, and patterns.
        """
        return {
            "bank": self._bank_num,
            "flex_count": self.flex_count,
            "parts": [self._parts[n].to_dict(include_scenes=include_scenes) for n in range(1, 5)],
            "patterns": [self._patterns[n].to_dict(include_steps=include_steps) for n in range(1, 17)],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bank":
        """Create a Bank from a dictionary."""
        bank = cls(
            bank_num=data.get("bank", 1),
            flex_count=data.get("flex_count", 0),
        )

        if "parts" in data:
            for part_data in data["parts"]:
                part = Part.from_dict(part_data)
                bank._parts[part.part_num] = part

        if "patterns" in data:
            for pattern_data in data["patterns"]:
                pattern = Pattern.from_dict(pattern_data)
                bank._patterns[pattern.pattern_num] = pattern

        return bank

    def __eq__(self, other) -> bool:
        """Check equality based on all contained objects."""
        if not isinstance(other, Bank):
            return NotImplemented
        if self._bank_num != other._bank_num:
            return False
        if self.flex_count != other.flex_count:
            return False
        if self._parts != other._parts:
            return False
        if self._patterns != other._patterns:
            return False
        return True

    def __repr__(self) -> str:
        return f"Bank(bank={self._bank_num}, flex_count={self.flex_count})"
