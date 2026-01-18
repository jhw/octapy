"""
Dynamics FX classes (Compressor).
"""

from .base import BaseFX


class CompressorFX(BaseFX):
    """
    Compressor effect container.

    Encoders:
        A: attack    - Attack time
        B: release   - Release time
        C: threshold - Threshold level
        D: ratio     - Compression ratio
        E: gain      - Makeup gain
        F: mix       - Wet/dry mix
    """

    @property
    def attack(self) -> int:
        """Get/set attack time (0-127)."""
        return self._get_param(0)

    @attack.setter
    def attack(self, value: int):
        self._set_param(0, value)

    @property
    def release(self) -> int:
        """Get/set release time (0-127)."""
        return self._get_param(1)

    @release.setter
    def release(self, value: int):
        self._set_param(1, value)

    @property
    def threshold(self) -> int:
        """Get/set threshold level (0-127)."""
        return self._get_param(2)

    @threshold.setter
    def threshold(self, value: int):
        self._set_param(2, value)

    @property
    def ratio(self) -> int:
        """Get/set compression ratio (0-127)."""
        return self._get_param(3)

    @ratio.setter
    def ratio(self, value: int):
        self._set_param(3, value)

    @property
    def gain(self) -> int:
        """Get/set makeup gain (0-127)."""
        return self._get_param(4)

    @gain.setter
    def gain(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)
