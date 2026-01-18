"""
Delay FX class.
"""

from .base import BaseFX


class DelayFX(BaseFX):
    """
    Delay effect container (FX2 only).

    Encoders:
        A: time      - Delay time
        B: feedback  - Feedback amount
        C: volume    - Delay volume
        D: base      - Base frequency
        E: width     - Stereo width
        F: send      - Send level
    """

    @property
    def time(self) -> int:
        """Get/set delay time (0-127)."""
        return self._get_param(0)

    @time.setter
    def time(self, value: int):
        self._set_param(0, value)

    @property
    def feedback(self) -> int:
        """Get/set feedback amount (0-127)."""
        return self._get_param(1)

    @feedback.setter
    def feedback(self, value: int):
        self._set_param(1, value)

    @property
    def volume(self) -> int:
        """Get/set delay volume (0-127)."""
        return self._get_param(2)

    @volume.setter
    def volume(self, value: int):
        self._set_param(2, value)

    @property
    def base(self) -> int:
        """Get/set base frequency (0-127)."""
        return self._get_param(3)

    @base.setter
    def base(self, value: int):
        self._set_param(3, value)

    @property
    def width(self) -> int:
        """Get/set stereo width (0-127)."""
        return self._get_param(4)

    @width.setter
    def width(self, value: int):
        self._set_param(4, value)

    @property
    def send(self) -> int:
        """Get/set send level (0-127)."""
        return self._get_param(5)

    @send.setter
    def send(self, value: int):
        self._set_param(5, value)
