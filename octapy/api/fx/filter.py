"""
Filter FX class.
"""

from .base import BaseFX


class FilterFX(BaseFX):
    """
    Filter effect container.

    Encoders:
        A: base     - Base frequency
        B: width    - Filter width
        C: q        - Resonance/Q
        D: depth    - Modulation depth
        E: attack   - Envelope attack
        F: decay    - Envelope decay
    """

    @property
    def base(self) -> int:
        """Get/set filter base frequency (0-127)."""
        return self._get_param(0)

    @base.setter
    def base(self, value: int):
        self._set_param(0, value)

    @property
    def width(self) -> int:
        """Get/set filter width (0-127)."""
        return self._get_param(1)

    @width.setter
    def width(self, value: int):
        self._set_param(1, value)

    @property
    def q(self) -> int:
        """Get/set filter Q/resonance (0-127)."""
        return self._get_param(2)

    @q.setter
    def q(self, value: int):
        self._set_param(2, value)

    @property
    def depth(self) -> int:
        """Get/set modulation depth (0-127)."""
        return self._get_param(3)

    @depth.setter
    def depth(self, value: int):
        self._set_param(3, value)

    @property
    def attack(self) -> int:
        """Get/set envelope attack (0-127)."""
        return self._get_param(4)

    @attack.setter
    def attack(self, value: int):
        self._set_param(4, value)

    @property
    def decay(self) -> int:
        """Get/set envelope decay (0-127)."""
        return self._get_param(5)

    @decay.setter
    def decay(self, value: int):
        self._set_param(5, value)
