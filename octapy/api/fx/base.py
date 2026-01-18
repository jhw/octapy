"""
Base classes for FX containers.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..part.audio import AudioPartTrack


class BaseFX(ABC):
    """
    Base class for FX containers.

    Provides typed access to FX parameters stored in the Part's track data.
    Subclasses define effect-specific property names.
    """

    # Offset within track params for FX1 (0) or FX2 (6)
    _FX1_BASE = 12  # AudioTrackParamsOffset.FX1_PARAM1
    _FX2_BASE = 18  # AudioTrackParamsOffset.FX2_PARAM1

    def __init__(self, part_track: "AudioPartTrack", slot: int):
        """
        Initialize FX container.

        Args:
            part_track: The AudioPartTrack this FX belongs to
            slot: 1 for FX1, 2 for FX2
        """
        self._part_track = part_track
        self._slot = slot
        self._base_offset = self._FX1_BASE if slot == 1 else self._FX2_BASE

    def _get_param(self, param_index: int) -> int:
        """Get FX parameter value (0-5 for params A-F)."""
        offset = self._part_track._track_params_offset() + self._base_offset + param_index
        return self._part_track._data[offset]

    def _set_param(self, param_index: int, value: int):
        """Set FX parameter value (0-5 for params A-F)."""
        offset = self._part_track._track_params_offset() + self._base_offset + param_index
        self._part_track._data[offset] = value & 0x7F


class OffFX(BaseFX):
    """FX container for OFF (no effect)."""
    pass
