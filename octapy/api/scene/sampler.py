"""
SamplerSceneTrack - scene track for Flex/Static machines.
"""

from __future__ import annotations

from typing import Optional

from ..._io import SceneParamsOffset
from .audio import AudioSceneTrack


class SamplerSceneTrack(AudioSceneTrack):
    """
    Scene track for Flex and Static machines.

    Adds playback page locks: pitch, start, length, rate, retrig, retrig time.
    Inherits AMP, FX1, FX2 locks from AudioSceneTrack.

    Usage:
        scene = part.scene(1)
        track = scene.sampler_track(1)

        # Set playback locks
        track.pitch = 72      # Lock pitch
        track.start = 0       # Lock start point
        track.length = 127    # Lock length

        # AMP/FX locks inherited
        track.amp_volume = 100
    """

    @property
    def pitch(self) -> Optional[int]:
        """Get/set pitch lock (None = no lock, 64 = no transpose)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM1)

    @pitch.setter
    def pitch(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM1, value)

    @property
    def start(self) -> Optional[int]:
        """Get/set start point lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM2)

    @start.setter
    def start(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM2, value)

    @property
    def length(self) -> Optional[int]:
        """Get/set length lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM3)

    @length.setter
    def length(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM3, value)

    @property
    def rate(self) -> Optional[int]:
        """Get/set playback rate lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM4)

    @rate.setter
    def rate(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM4, value)

    @property
    def retrig(self) -> Optional[int]:
        """Get/set retrig lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM5)

    @retrig.setter
    def retrig(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM5, value)

    @property
    def retrig_time(self) -> Optional[int]:
        """Get/set retrig time lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM6)

    @retrig_time.setter
    def retrig_time(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM6, value)
