"""
BaseSceneTrack - abstract base class for scene track locks.
"""

from __future__ import annotations

from abc import ABC
from typing import Optional

from ..._io import (
    SceneOffset,
    SceneParamsOffset,
    SCENE_SIZE,
    SCENE_PARAMS_SIZE,
    SCENE_LOCK_DISABLED,
)


class BaseSceneTrack(ABC):
    """
    Abstract base class for scene track locks.

    Provides shared functionality for accessing scene parameter locks.
    Scene locks use 255 to indicate "no lock" (use Part default).

    Subclasses provide machine-specific playback page properties.
    """

    def __init__(self, scene: Scene, track_num: int):
        self._scene = scene
        self._track_num = track_num

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._scene._part._bank._bank_file._data

    def _part_offset(self) -> int:
        """Get the byte offset for this scene's part in the bank file."""
        return self._scene._part._bank._bank_file.part_offset(self._scene._part._part_num)

    def _scene_track_offset(self) -> int:
        """Get the byte offset for this track within this scene."""
        return (
            self._part_offset() +
            SceneOffset.SCENES +
            (self._scene._scene_num - 1) * SCENE_SIZE +
            (self._track_num - 1) * SCENE_PARAMS_SIZE
        )

    def _get_lock(self, offset: int) -> Optional[int]:
        """
        Get a scene lock value.

        Returns None if the parameter is not locked (255),
        otherwise returns the locked value.
        """
        value = self._data[self._scene_track_offset() + offset]
        return None if value == SCENE_LOCK_DISABLED else value

    def _set_lock(self, offset: int, value: Optional[int]):
        """
        Set a scene lock value.

        Pass None to clear the lock (set to 255).
        Pass a value to set the lock destination.
        """
        if value is None:
            self._data[self._scene_track_offset() + offset] = SCENE_LOCK_DISABLED
        else:
            self._data[self._scene_track_offset() + offset] = value & 0x7F

    def clear_all_locks(self):
        """Clear all locks for this track (set all to 255)."""
        offset = self._scene_track_offset()
        for i in range(SCENE_PARAMS_SIZE):
            self._data[offset + i] = SCENE_LOCK_DISABLED
