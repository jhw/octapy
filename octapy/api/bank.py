"""
Bank class for managing patterns and parts.
"""

from __future__ import annotations

from typing import Dict

from .._io import BankFile
from .part import Part
from .pattern import Pattern


class Bank:
    """
    Pythonic interface for an Octatrack Bank.

    A Bank contains 16 patterns and 4 parts.
    Each project has 16 banks.

    Usage:
        bank = project.bank(1)
        part = bank.part(1)
        pattern = bank.pattern(1)
    """

    def __init__(self, project: "Project", bank_num: int, bank_file: BankFile):
        self._project = project
        self._bank_num = bank_num
        self._bank_file = bank_file
        self._parts: Dict[int, Part] = {}
        self._patterns: Dict[int, Pattern] = {}

    def part(self, part_num: int) -> Part:
        """
        Get a Part (1-4).

        Args:
            part_num: Part number (1-4)

        Returns:
            Part instance for configuring track machines
        """
        if part_num not in self._parts:
            self._parts[part_num] = Part(self, part_num)
        return self._parts[part_num]

    def pattern(self, pattern_num: int) -> Pattern:
        """
        Get a Pattern (1-16).

        Args:
            pattern_num: Pattern number (1-16)

        Returns:
            Pattern instance for configuring triggers
        """
        if pattern_num not in self._patterns:
            self._patterns[pattern_num] = Pattern(self, pattern_num)
        return self._patterns[pattern_num]

    @property
    def flex_count(self) -> int:
        """Get/set the flex slot counter."""
        return self._bank_file.flex_count

    @flex_count.setter
    def flex_count(self, value: int):
        self._bank_file.flex_count = value

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
            "parts": [self.part(n).to_dict(include_scenes=include_scenes) for n in range(1, 5)],
            "patterns": [self.pattern(n).to_dict(include_steps=include_steps) for n in range(1, 17)],
        }
