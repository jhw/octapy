"""
MidiPatternTrack - MIDI track sequence data.
"""

from __future__ import annotations

from ..._io import (
    PatternOffset,
    MidiTrackTrigsOffset,
    MIDI_TRACK_PATTERN_SIZE,
)
from ..step import MidiStep
from .base import BasePatternTrack


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
