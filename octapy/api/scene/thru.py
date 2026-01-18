"""
ThruSceneTrack - scene track for Thru machines.
"""

from __future__ import annotations

from typing import Optional

from ..._io import SceneParamsOffset
from .audio import AudioSceneTrack


class ThruSceneTrack(AudioSceneTrack):
    """
    Scene track for Thru machines.

    Adds playback page locks: in_ab, vol_ab, in_cd, vol_cd.
    Inherits AMP, FX1, FX2 locks from AudioSceneTrack.

    Usage:
        scene = part.scene(1)
        track = scene.thru_track(1)

        # Set input/volume locks
        track.in_ab = 1
        track.vol_ab = 64
    """

    @property
    def in_ab(self) -> Optional[int]:
        """Get/set input A/B lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM1)

    @in_ab.setter
    def in_ab(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM1, value)

    @property
    def vol_ab(self) -> Optional[int]:
        """Get/set volume A/B lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM2)

    @vol_ab.setter
    def vol_ab(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM2, value)

    @property
    def in_cd(self) -> Optional[int]:
        """Get/set input C/D lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM4)

    @in_cd.setter
    def in_cd(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM4, value)

    @property
    def vol_cd(self) -> Optional[int]:
        """Get/set volume C/D lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM5)

    @vol_cd.setter
    def vol_cd(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM5, value)
