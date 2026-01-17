"""
AudioPatternTrack - Audio track sequence data.
"""

from __future__ import annotations

from typing import Union

from ..._io import AudioTrackOffset
from ..enums import MachineType
from ..step import AudioStep, SamplerStep
from .base import BasePatternTrack


class AudioPatternTrack(BasePatternTrack):
    """
    Audio sequence data for a track within a Pattern.

    Provides access to 64 steps and their trigger states.
    This is separate from AudioPartTrack which handles sound configuration.

    Returns SamplerStep for Flex/Static machine tracks (with volume, pitch,
    sample_lock p-locks) and AudioStep for other machine types.

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

    def _is_sampler_track(self) -> bool:
        """Check if this track uses a sample-based machine (Flex/Static)."""
        part_num = self._pattern.part
        part = self._pattern._bank.part(part_num)
        track = part.track(self._track_num)
        return track.machine_type in (MachineType.FLEX, MachineType.STATIC)

    def _create_step(self, step_num: int) -> Union[AudioStep, SamplerStep]:
        """Create appropriate step type based on machine type."""
        if self._is_sampler_track():
            return SamplerStep(self, step_num)
        return AudioStep(self, step_num)

    def step(self, step_num: int) -> Union[AudioStep, SamplerStep]:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            SamplerStep for Flex/Static machines (with volume, pitch, sample_lock)
            AudioStep for other machine types (Thru, Neighbor, Pickup)
        """
        return super().step(step_num)
