"""
Pattern - Container class for pattern sequence data.
"""

from __future__ import annotations

from typing import Dict

from ..._io import PatternOffset
from .audio import AudioPatternTrack
from .midi import MidiPatternTrack


class Pattern:
    """
    Pythonic interface for an Octatrack Pattern.

    A Pattern holds sequence data for 8 tracks and is assigned to a Part.
    Each bank has 16 patterns.

    Usage:
        pattern = bank.pattern(1)
        pattern.part = 1  # Assign to Part 1
        pattern.track(1).active_steps = [1, 5, 9, 13]
        pattern.track(1).step(5).condition = TrigCondition.FILL
    """

    def __init__(self, bank: "Bank", pattern_num: int):
        self._bank = bank
        self._pattern_num = pattern_num
        self._tracks: Dict[int, AudioPatternTrack] = {}
        self._midi_tracks: Dict[int, MidiPatternTrack] = {}

    def _pattern_offset(self) -> int:
        """Get the byte offset for this pattern in the bank file."""
        return self._bank._bank_file.pattern_offset(self._pattern_num)

    @property
    def part(self) -> int:
        """Get/set which Part this pattern uses (1-4)."""
        data = self._bank._bank_file._data
        offset = self._pattern_offset() + PatternOffset.PART_ASSIGNMENT
        return data[offset] + 1  # Convert to 1-indexed

    @part.setter
    def part(self, value: int):
        data = self._bank._bank_file._data
        offset = self._pattern_offset() + PatternOffset.PART_ASSIGNMENT
        data[offset] = (value - 1) & 0x03  # Convert to 0-indexed

    def track(self, track_num: int) -> AudioPatternTrack:
        """
        Get sequence data for a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioPatternTrack instance for configuring steps
        """
        if track_num not in self._tracks:
            self._tracks[track_num] = AudioPatternTrack(self, track_num)
        return self._tracks[track_num]

    def midi_track(self, track_num: int) -> MidiPatternTrack:
        """
        Get MIDI sequence data for a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPatternTrack instance for configuring MIDI steps
        """
        if track_num not in self._midi_tracks:
            self._midi_tracks[track_num] = MidiPatternTrack(self, track_num)
        return self._midi_tracks[track_num]
