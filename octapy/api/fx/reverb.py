"""
Reverb FX classes (Plate, Spring, Dark).
"""

from .base import BaseFX


class PlateReverbFX(BaseFX):
    """
    Plate reverb effect container (FX2 only).

    Encoders:
        A: time      - Reverb time
        B: damp      - Damping
        C: gate      - Gate
        D: high_pass - High-pass filter
        E: low_pass  - Low-pass filter
        F: mix       - Wet/dry mix
    """

    @property
    def time(self) -> int:
        """Get/set reverb time (0-127)."""
        return self._get_param(0)

    @time.setter
    def time(self, value: int):
        self._set_param(0, value)

    @property
    def damp(self) -> int:
        """Get/set damping (0-127)."""
        return self._get_param(1)

    @damp.setter
    def damp(self, value: int):
        self._set_param(1, value)

    @property
    def gate(self) -> int:
        """Get/set gate (0-127)."""
        return self._get_param(2)

    @gate.setter
    def gate(self, value: int):
        self._set_param(2, value)

    @property
    def high_pass(self) -> int:
        """Get/set high-pass filter (0-127)."""
        return self._get_param(3)

    @high_pass.setter
    def high_pass(self, value: int):
        self._set_param(3, value)

    @property
    def low_pass(self) -> int:
        """Get/set low-pass filter (0-127)."""
        return self._get_param(4)

    @low_pass.setter
    def low_pass(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)


class SpringReverbFX(BaseFX):
    """
    Spring reverb effect container (FX2 only).

    Encoders:
        A: time      - Reverb time
        B: (unused)
        C: (unused)
        D: high_pass - High-pass filter
        E: low_pass  - Low-pass filter
        F: mix       - Wet/dry mix
    """

    @property
    def time(self) -> int:
        """Get/set reverb time (0-127)."""
        return self._get_param(0)

    @time.setter
    def time(self, value: int):
        self._set_param(0, value)

    @property
    def high_pass(self) -> int:
        """Get/set high-pass filter (0-127)."""
        return self._get_param(3)

    @high_pass.setter
    def high_pass(self, value: int):
        self._set_param(3, value)

    @property
    def low_pass(self) -> int:
        """Get/set low-pass filter (0-127)."""
        return self._get_param(4)

    @low_pass.setter
    def low_pass(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)


class DarkReverbFX(BaseFX):
    """
    Dark reverb effect container (FX2 only).

    Encoders:
        A: time      - Reverb time
        B: shug      - Shug parameter
        C: shuf      - Shuf parameter
        D: high_pass - High-pass filter
        E: low_pass  - Low-pass filter
        F: mix       - Wet/dry mix
    """

    @property
    def time(self) -> int:
        """Get/set reverb time (0-127)."""
        return self._get_param(0)

    @time.setter
    def time(self, value: int):
        self._set_param(0, value)

    @property
    def shug(self) -> int:
        """Get/set shug parameter (0-127)."""
        return self._get_param(1)

    @shug.setter
    def shug(self, value: int):
        self._set_param(1, value)

    @property
    def shuf(self) -> int:
        """Get/set shuf parameter (0-127)."""
        return self._get_param(2)

    @shuf.setter
    def shuf(self, value: int):
        self._set_param(2, value)

    @property
    def high_pass(self) -> int:
        """Get/set high-pass filter (0-127)."""
        return self._get_param(3)

    @high_pass.setter
    def high_pass(self, value: int):
        self._set_param(3, value)

    @property
    def low_pass(self) -> int:
        """Get/set low-pass filter (0-127)."""
        return self._get_param(4)

    @low_pass.setter
    def low_pass(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)
