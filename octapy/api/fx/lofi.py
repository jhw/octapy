"""
Lo-fi FX class.
"""

from .base import BaseFX


class LofiFX(BaseFX):
    """
    Lo-fi effect container.

    Encoders:
        A: dist  - Distortion
        B: (unused)
        C: amf   - AMF parameter
        D: srr   - Sample rate reduction
        E: brr   - Bit rate reduction
        F: amd   - AMD parameter
    """

    @property
    def dist(self) -> int:
        """Get/set distortion (0-127)."""
        return self._get_param(0)

    @dist.setter
    def dist(self, value: int):
        self._set_param(0, value)

    @property
    def amf(self) -> int:
        """Get/set AMF parameter (0-127)."""
        return self._get_param(2)

    @amf.setter
    def amf(self, value: int):
        self._set_param(2, value)

    @property
    def srr(self) -> int:
        """Get/set sample rate reduction (0-127)."""
        return self._get_param(3)

    @srr.setter
    def srr(self, value: int):
        self._set_param(3, value)

    @property
    def brr(self) -> int:
        """Get/set bit rate reduction (0-127)."""
        return self._get_param(4)

    @brr.setter
    def brr(self, value: int):
        self._set_param(4, value)

    @property
    def amd(self) -> int:
        """Get/set AMD parameter (0-127)."""
        return self._get_param(5)

    @amd.setter
    def amd(self, value: int):
        self._set_param(5, value)
