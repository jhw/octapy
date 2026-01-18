"""
Spatializer FX class.
"""

from .base import BaseFX


class SpatializerFX(BaseFX):
    """
    Spatializer effect container.

    Encoders:
        A: input      - Input level
        B: depth      - Spatial depth
        C: width      - Stereo width
        D: high_pass  - High-pass filter
        E: low_pass   - Low-pass filter
        F: send       - Send level
    """

    @property
    def input(self) -> int:
        """Get/set input level (0-127)."""
        return self._get_param(0)

    @input.setter
    def input(self, value: int):
        self._set_param(0, value)

    @property
    def depth(self) -> int:
        """Get/set spatial depth (0-127)."""
        return self._get_param(1)

    @depth.setter
    def depth(self, value: int):
        self._set_param(1, value)

    @property
    def width(self) -> int:
        """Get/set stereo width (0-127)."""
        return self._get_param(2)

    @width.setter
    def width(self, value: int):
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
    def send(self) -> int:
        """Get/set send level (0-127)."""
        return self._get_param(5)

    @send.setter
    def send(self, value: int):
        self._set_param(5, value)
