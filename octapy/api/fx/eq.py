"""
EQ FX classes.
"""

from .base import BaseFX


class EqFX(BaseFX):
    """
    Parametric EQ effect container.

    Encoders:
        A: freq1  - Band 1 frequency
        B: gain1  - Band 1 gain
        C: q1     - Band 1 Q
        D: freq2  - Band 2 frequency
        E: gain2  - Band 2 gain
        F: q2     - Band 2 Q
    """

    @property
    def freq1(self) -> int:
        """Get/set band 1 frequency (0-127)."""
        return self._get_param(0)

    @freq1.setter
    def freq1(self, value: int):
        self._set_param(0, value)

    @property
    def gain1(self) -> int:
        """Get/set band 1 gain (0-127)."""
        return self._get_param(1)

    @gain1.setter
    def gain1(self, value: int):
        self._set_param(1, value)

    @property
    def q1(self) -> int:
        """Get/set band 1 Q (0-127)."""
        return self._get_param(2)

    @q1.setter
    def q1(self, value: int):
        self._set_param(2, value)

    @property
    def freq2(self) -> int:
        """Get/set band 2 frequency (0-127)."""
        return self._get_param(3)

    @freq2.setter
    def freq2(self, value: int):
        self._set_param(3, value)

    @property
    def gain2(self) -> int:
        """Get/set band 2 gain (0-127)."""
        return self._get_param(4)

    @gain2.setter
    def gain2(self, value: int):
        self._set_param(4, value)

    @property
    def q2(self) -> int:
        """Get/set band 2 Q (0-127)."""
        return self._get_param(5)

    @q2.setter
    def q2(self, value: int):
        self._set_param(5, value)


class DjEqFX(BaseFX):
    """
    DJ EQ effect container (3-band).

    Encoders:
        A: low_shelf_freq   - Low shelf frequency
        B: (unused)
        C: high_shelf_freq  - High shelf frequency
        D: low_gain         - Low band gain
        E: mid_gain         - Mid band gain
        F: high_gain        - High band gain
    """

    @property
    def low_shelf_freq(self) -> int:
        """Get/set low shelf frequency (0-127)."""
        return self._get_param(0)

    @low_shelf_freq.setter
    def low_shelf_freq(self, value: int):
        self._set_param(0, value)

    @property
    def high_shelf_freq(self) -> int:
        """Get/set high shelf frequency (0-127)."""
        return self._get_param(2)

    @high_shelf_freq.setter
    def high_shelf_freq(self, value: int):
        self._set_param(2, value)

    @property
    def low_gain(self) -> int:
        """Get/set low band gain (0-127)."""
        return self._get_param(3)

    @low_gain.setter
    def low_gain(self, value: int):
        self._set_param(3, value)

    @property
    def mid_gain(self) -> int:
        """Get/set mid band gain (0-127)."""
        return self._get_param(4)

    @mid_gain.setter
    def mid_gain(self, value: int):
        self._set_param(4, value)

    @property
    def high_gain(self) -> int:
        """Get/set high band gain (0-127)."""
        return self._get_param(5)

    @high_gain.setter
    def high_gain(self, value: int):
        self._set_param(5, value)
