"""
FlexStep - Step class for Flex sample machines.
"""

from __future__ import annotations

from typing import Optional

from ..._io import PlockOffset
from .sampler import SamplerStep


class FlexStep(SamplerStep):
    """
    Step within a Flex sample machine track.

    Extends SamplerStep with Flex-specific p-locks for sample length and
    reverse playback. These work with the Flex defaults:
    - length_mode = TIME (LEN encoder active)
    - length = 127 (full sample)
    - rate = 127 (forward direction)

    Usage:
        step = pattern.track(1).step(5)  # Returns FlexStep for Flex machines
        step.active = True
        step.length = 0.5     # P-lock length to 50% of sample
        step.reverse = True   # P-lock to reverse playback
    """

    # === Flex-specific P-lock properties ===

    @property
    def length(self) -> Optional[float]:
        """
        Get/set p-locked sample length for this step.

        Value range: 0.0-1.0 (fraction of full sample length)
        Internally quantized to 0-127.

        Returns None if no p-lock is set (uses Part default of 127/full).
        Set to None to clear the p-lock.

        Note: Requires length_mode = TIME on the Part track to have effect.
        """
        raw = self._get_plock(PlockOffset.MACHINE_PARAM3)
        if raw is None:
            return None
        return raw / 127.0

    @length.setter
    def length(self, value: Optional[float]):
        if value is None:
            self._set_plock(PlockOffset.MACHINE_PARAM3, None)
        else:
            # Clamp to 0-1 and quantize to 0-127
            clamped = max(0.0, min(1.0, value))
            quantized = round(clamped * 127)
            self._set_plock(PlockOffset.MACHINE_PARAM3, quantized)

    @property
    def reverse(self) -> Optional[bool]:
        """
        Get/set p-locked reverse playback for this step.

        True = reverse (rate=0), False = forward (rate=127)
        Returns None if no p-lock is set (uses Part default of forward).
        Set to None to clear the p-lock.

        Note: Only these two values (0 and 127) are supported for p-locking.
        The Part track rate should be set to 127 (forward) to allow
        p-locking to reverse.
        """
        raw = self._get_plock(PlockOffset.MACHINE_PARAM4)
        if raw is None:
            return None
        return raw == 0

    @reverse.setter
    def reverse(self, value: Optional[bool]):
        if value is None:
            self._set_plock(PlockOffset.MACHINE_PARAM4, None)
        else:
            # True = reverse (0), False = forward (127)
            self._set_plock(PlockOffset.MACHINE_PARAM4, 0 if value else 127)
