"""
AudioStep - Base audio track step class.
"""

from __future__ import annotations

from ..._io import (
    AudioTrackOffset,
    PLOCK_SIZE,
)
from .base import BaseStep


class AudioStep(BaseStep):
    """
    Base step class for audio pattern tracks.

    Provides audio track offset constants for trigger and p-lock data.
    This is the base class for all audio track steps.

    For sample-specific p-locks (volume, pitch, sample_lock), use SamplerStep
    which is returned automatically for Flex/Static machine tracks.

    Usage:
        step = pattern.track(1).step(5)
        step.active = True
        step.condition = TrigCondition.FILL
        step.probability = 0.5  # 50% trigger probability
    """

    @property
    def _trig_offset(self) -> int:
        return AudioTrackOffset.TRIG_TRIGGER

    @property
    def _trigless_offset(self) -> int:
        return AudioTrackOffset.TRIG_TRIGLESS

    @property
    def _plocks_offset(self) -> int:
        return AudioTrackOffset.PLOCKS

    @property
    def _plock_size(self) -> int:
        return PLOCK_SIZE

    @property
    def _conditions_offset(self) -> int:
        return AudioTrackOffset.TRIG_CONDITIONS
