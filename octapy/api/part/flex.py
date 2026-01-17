"""
FlexPartTrack - Flex machine track configuration.
"""

from __future__ import annotations

from ..._io import MachineParamsOffset
from .sampler import SamplerPartTrack


class FlexPartTrack(SamplerPartTrack):
    """
    Flex machine track configuration.

    Flex machines load samples into RAM for manipulation.
    See SamplerPartTrack for encoder layout documentation.

    Usage:
        track = part.flex_track(1)
        track.pitch = 64          # No transpose
        track.start = 0           # Sample start
        track.retrig_time = 79    # Retrig time (default)
    """

    def _values_offset(self) -> int:
        """Get offset for Flex params values."""
        return self._machine_params_values_offset(MachineParamsOffset.FLEX)

    def _setup_offset(self) -> int:
        """Get offset for Flex params setup."""
        return self._machine_params_setup_offset(MachineParamsOffset.FLEX)
