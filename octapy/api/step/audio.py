"""
AudioStep - Audio track step class.
"""

from __future__ import annotations

from typing import Optional

from ..._io import (
    AudioTrackOffset,
    PlockOffset,
    PLOCK_SIZE,
)
from .base import BaseStep


class AudioStep(BaseStep):
    """
    Individual step within an audio pattern track.

    Provides access to step properties including active state, trigless state,
    condition, and p-locks (per-step parameter values).

    Usage:
        step = pattern.track(1).step(5)
        step.active = True
        step.condition = TrigCondition.FILL
        step.volume = 100  # P-lock volume
        step.pitch = 64    # P-lock pitch (64 = no transpose)
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

    # === Audio P-lock properties ===

    @property
    def volume(self) -> Optional[int]:
        """
        Get/set p-locked volume for this step.

        Value range: 0-127 (0 = silent, 127 = max)
        Returns None if no p-lock is set (uses track default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(PlockOffset.AMP_VOL)

    @volume.setter
    def volume(self, value: Optional[int]):
        self._set_plock(PlockOffset.AMP_VOL, value)

    @property
    def pitch(self) -> Optional[int]:
        """
        Get/set p-locked pitch/note for this step.

        Value range: 0-127 (64 = no transpose, <64 = lower, >64 = higher)
        This is the PTCH parameter on the Playback page.
        Returns None if no p-lock is set (uses track default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(PlockOffset.MACHINE_PARAM1)

    @pitch.setter
    def pitch(self, value: Optional[int]):
        self._set_plock(PlockOffset.MACHINE_PARAM1, value)

    @property
    def sample_lock(self) -> Optional[int]:
        """
        Get/set p-locked sample slot for this step (Flex machines).

        Value range: 0-127 (0-indexed slot number)
        Returns None if no sample lock is set.
        Set to None to clear the sample lock.
        """
        return self._get_plock(PlockOffset.FLEX_SLOT_ID)

    @sample_lock.setter
    def sample_lock(self, value: Optional[int]):
        self._set_plock(PlockOffset.FLEX_SLOT_ID, value)
