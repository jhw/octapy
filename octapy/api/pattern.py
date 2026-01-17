"""
Pattern and AudioPatternTrack classes for sequence programming.
"""

from typing import TYPE_CHECKING, Dict, List

from .._io import AudioTrackOffset, PatternOffset
from .step import AudioStep, _trig_mask_to_steps, _steps_to_trig_mask

if TYPE_CHECKING:
    from .bank import Bank


class AudioPatternTrack:
    """
    Audio sequence data for a track within a Pattern.

    Provides access to 64 steps and their trigger states.
    This is separate from AudioPartTrack which handles sound configuration.

    Usage:
        track = pattern.track(1)
        track.active_steps = [1, 5, 9, 13]
        track.step(5).condition = TrigCondition.FILL
    """

    def __init__(self, pattern: "Pattern", track_num: int):
        self._pattern = pattern
        self._track_num = track_num
        self._steps: Dict[int, AudioStep] = {}

    def _track_offset(self) -> int:
        """Get the byte offset for this track in the bank file."""
        return self._pattern._bank._bank_file.audio_track_offset(
            self._pattern._pattern_num, self._track_num
        )

    def step(self, step_num: int) -> AudioStep:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            AudioStep instance for this position
        """
        if step_num not in self._steps:
            self._steps[step_num] = AudioStep(self, step_num)
        return self._steps[step_num]

    @property
    def active_steps(self) -> List[int]:
        """Get/set active trigger steps (1-indexed list)."""
        data = self._pattern._bank._bank_file._data
        offset = self._track_offset() + AudioTrackOffset.TRIG_TRIGGER
        return _trig_mask_to_steps(data, offset)

    @active_steps.setter
    def active_steps(self, value: List[int]):
        data = self._pattern._bank._bank_file._data
        offset = self._track_offset() + AudioTrackOffset.TRIG_TRIGGER
        _steps_to_trig_mask(data, offset, value)

    @property
    def trigless_steps(self) -> List[int]:
        """Get/set trigless (envelope) steps (1-indexed list)."""
        data = self._pattern._bank._bank_file._data
        offset = self._track_offset() + AudioTrackOffset.TRIG_TRIGLESS
        return _trig_mask_to_steps(data, offset)

    @trigless_steps.setter
    def trigless_steps(self, value: List[int]):
        data = self._pattern._bank._bank_file._data
        offset = self._track_offset() + AudioTrackOffset.TRIG_TRIGLESS
        _steps_to_trig_mask(data, offset, value)


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
