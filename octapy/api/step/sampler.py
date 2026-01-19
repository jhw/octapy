"""
SamplerStep - Step class for Flex/Static sample machines.
"""

from __future__ import annotations

from typing import Optional

from ..._io import PlockOffset
from .audio import AudioStep


class SamplerStep(AudioStep):
    """
    Step within a Flex or Static sample machine track.

    Extends AudioStep with sample-specific p-locks (volume, pitch, sample lock).
    These p-locks only apply to sample-based machines (Flex/Static), not to
    Thru, Neighbor, or Pickup machines.

    Usage:
        step = pattern.track(1).step(5)  # Returns SamplerStep for Flex/Static
        step.active = True
        step.condition = TrigCondition.FILL
        step.volume = 100  # P-lock volume
        step.pitch = 64    # P-lock pitch (64 = no transpose)
        step.sample_lock = 5  # P-lock to sample slot 5
    """

    # === Sampler P-lock properties ===

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
        Get/set p-locked sample slot for this step.

        Value range: 0-127 (0-indexed slot number)
        Returns None if no sample lock is set.
        Set to None to clear the sample lock.
        """
        return self._get_plock(PlockOffset.FLEX_SLOT_ID)

    @sample_lock.setter
    def sample_lock(self, value: Optional[int]):
        self._set_plock(PlockOffset.FLEX_SLOT_ID, value)

    def to_dict(self) -> dict:
        """
        Convert step state to dictionary including sampler p-locks.

        Extends base to_dict with volume, pitch, sample_lock.
        """
        result = super().to_dict()
        # Only include p-locks if set
        if self.volume is not None:
            result["volume"] = self.volume
        if self.pitch is not None:
            result["pitch"] = self.pitch
        if self.sample_lock is not None:
            result["sample_lock"] = self.sample_lock
        return result
