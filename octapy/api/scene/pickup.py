"""
PickupSceneTrack - scene track for Pickup machines.
"""

from __future__ import annotations

from typing import Optional

from ..._io import SceneParamsOffset
from .audio import AudioSceneTrack


class PickupSceneTrack(AudioSceneTrack):
    """
    Scene track for Pickup machines.

    Adds playback page locks: pitch, direction, length, gain, operation.
    Inherits AMP, FX1, FX2 locks from AudioSceneTrack.

    Usage:
        scene = part.scene(1)
        track = scene.pickup_track(1)

        # Set playback locks
        track.pitch = 64
        track.gain = 80
    """

    @property
    def pitch(self) -> Optional[int]:
        """Get/set pitch lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM1)

    @pitch.setter
    def pitch(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM1, value)

    @property
    def direction(self) -> Optional[int]:
        """Get/set direction lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM2)

    @direction.setter
    def direction(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM2, value)

    @property
    def length(self) -> Optional[int]:
        """Get/set length lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM3)

    @length.setter
    def length(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM3, value)

    @property
    def gain(self) -> Optional[int]:
        """Get/set gain lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM5)

    @gain.setter
    def gain(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM5, value)

    @property
    def operation(self) -> Optional[int]:
        """Get/set operation mode lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM6)

    @operation.setter
    def operation(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM6, value)
