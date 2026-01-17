"""
AudioPatternTrack - Audio track sequence data.
"""

from __future__ import annotations

from ..._io import AudioTrackOffset
from ..step import AudioStep
from .base import BasePatternTrack


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
