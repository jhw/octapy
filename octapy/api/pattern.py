"""
Pattern and PatternTrack classes for sequence programming.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from .._io import (
    AudioTrackOffset,
    PatternOffset,
    MidiTrackTrigsOffset,
    MIDI_TRACK_PATTERN_SIZE,
)
from .step import AudioStep, MidiStep, BaseStep, _trig_mask_to_steps, _steps_to_trig_mask


# =============================================================================
# BasePatternTrack Class
# =============================================================================

class BasePatternTrack(ABC):
    """
    Abstract base class for pattern track sequence data.

    Provides shared functionality for step access and trig masks.
    Subclasses provide offset constants and step class.
    """

    def __init__(self, pattern: "Pattern", track_num: int):
        self._pattern = pattern
        self._track_num = track_num
        self._steps: Dict[int, BaseStep] = {}

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._pattern._bank._bank_file._data

    @abstractmethod
    def _track_offset(self) -> int:
        """Get the byte offset for this track in the bank file."""
        pass

    @property
    @abstractmethod
    def _trig_offset(self) -> int:
        """Offset to TRIG_TRIGGER within the track."""
        pass

    @property
    @abstractmethod
    def _trigless_offset(self) -> int:
        """Offset to TRIG_TRIGLESS within the track."""
        pass

    @abstractmethod
    def _create_step(self, step_num: int) -> BaseStep:
        """Create a step instance for this track type."""
        pass

    def step(self, step_num: int) -> BaseStep:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            Step instance for this position
        """
        if step_num not in self._steps:
            self._steps[step_num] = self._create_step(step_num)
        return self._steps[step_num]

    @property
    def active_steps(self) -> List[int]:
        """Get/set active trigger steps (1-indexed list)."""
        offset = self._track_offset() + self._trig_offset
        return _trig_mask_to_steps(self._data, offset)

    @active_steps.setter
    def active_steps(self, value: List[int]):
        offset = self._track_offset() + self._trig_offset
        _steps_to_trig_mask(self._data, offset, value)

    @property
    def trigless_steps(self) -> List[int]:
        """Get/set trigless (envelope) steps (1-indexed list)."""
        offset = self._track_offset() + self._trigless_offset
        return _trig_mask_to_steps(self._data, offset)

    @trigless_steps.setter
    def trigless_steps(self, value: List[int]):
        offset = self._track_offset() + self._trigless_offset
        _steps_to_trig_mask(self._data, offset, value)


# =============================================================================
# AudioPatternTrack Class
# =============================================================================

class AudioPatternTrack(BasePatternTrack):
    """
    Audio sequence data for a track within a Pattern.

    Provides access to 64 steps and their trigger states.
    This is separate from AudioPartTrack which handles sound configuration.

    Usage:
        track = pattern.track(1)
        track.active_steps = [1, 5, 9, 13]
        track.step(5).condition = TrigCondition.FILL
    """

    def _track_offset(self) -> int:
        """Get the byte offset for this track in the bank file."""
        return self._pattern._bank._bank_file.audio_track_offset(
            self._pattern._pattern_num, self._track_num
        )

    @property
    def _trig_offset(self) -> int:
        return AudioTrackOffset.TRIG_TRIGGER

    @property
    def _trigless_offset(self) -> int:
        return AudioTrackOffset.TRIG_TRIGLESS

    def _create_step(self, step_num: int) -> AudioStep:
        return AudioStep(self, step_num)

    def step(self, step_num: int) -> AudioStep:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            AudioStep instance for this position
        """
        return super().step(step_num)


# =============================================================================
# MidiPatternTrack Class
# =============================================================================

class MidiPatternTrack(BasePatternTrack):
    """
    MIDI sequence data for a track within a Pattern.

    Provides access to 64 steps and their trigger states for MIDI sequencing.
    This is separate from MidiPartTrack which handles sound/channel configuration.

    Usage:
        midi_track = pattern.midi_track(1)
        midi_track.active_steps = [1, 5, 9, 13]
        midi_track.step(5).note = 60  # Middle C
        midi_track.step(5).velocity = 100
    """

    def _track_offset(self) -> int:
        """Get the byte offset for this MIDI track in the bank file."""
        pattern_offset = self._pattern._bank._bank_file.pattern_offset(
            self._pattern._pattern_num
        )
        return (pattern_offset +
                PatternOffset.MIDI_TRACKS +
                (self._track_num - 1) * MIDI_TRACK_PATTERN_SIZE)

    @property
    def _trig_offset(self) -> int:
        return MidiTrackTrigsOffset.TRIG_TRIGGER

    @property
    def _trigless_offset(self) -> int:
        return MidiTrackTrigsOffset.TRIG_TRIGLESS

    def _create_step(self, step_num: int) -> MidiStep:
        return MidiStep(self, step_num)

    def step(self, step_num: int) -> MidiStep:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            MidiStep instance for this position
        """
        return super().step(step_num)


# =============================================================================
# Pattern Class
# =============================================================================

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
