"""
StaticPartTrack - Static machine track configuration.
"""

from __future__ import annotations

from ..._io import MachineParamsOffset
from .sampler import SamplerPartTrack


class StaticPartTrack(SamplerPartTrack):
    """
    Static machine track configuration.

    Static machines stream samples from the CF card.
    See SamplerPartTrack for encoder layout documentation.

    Usage:
        track = part.static_track(1)
        track.pitch = 64
        track.start = 0
    """

    def _values_offset(self) -> int:
        """Get offset for Static params values."""
        return self._machine_params_values_offset(MachineParamsOffset.STATIC)

    def _setup_offset(self) -> int:
        """Get offset for Static params setup."""
        return self._machine_params_setup_offset(MachineParamsOffset.STATIC)
