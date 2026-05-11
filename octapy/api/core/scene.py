"""
Scene - standalone scene container with 8 AudioSceneTrack objects.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Part binary data.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..._io import (
    SCENE_SIZE,
    SCENE_PARAMS_SIZE,
    SCENE_LOCK_DISABLED,
    SCENE_XLV_SIZE,
)
from .audio.scene_track import AudioSceneTrack


# Number of crossfader slots in the SceneXlvAssignments block (one per audio track).
_SCENE_XLV_TRACK_COUNT = 8


class Scene:
    """
    Scene containing parameter locks for all 8 tracks.

    This is a standalone object that owns its 256-byte data buffer
    (8 tracks * 32 bytes per track).

    Scene locks are used for crossfader morphing between Part defaults and scene values.

    Usage:
        # Create with constructor arguments
        scene = Scene(scene_num=1)
        scene.track(1).amp_volume = 100
        scene.track(1).pitch = 72

        # Read from Part binary (called by Part)
        scene = Scene.read(scene_num, scene_data)

        # Write to binary
        data = scene.write()
    """

    def __init__(
        self,
        scene_num: int = 1,
        tracks: Optional[List[AudioSceneTrack]] = None,
    ):
        """
        Create a Scene with optional track locks.

        Args:
            scene_num: Scene number (1-16)
            tracks: Optional list of 8 AudioSceneTrack objects
        """
        self._scene_num = scene_num
        # Initialize all locks to disabled
        self._data = bytearray([SCENE_LOCK_DISABLED] * SCENE_SIZE)
        # Crossfader (XLV) assignments — one byte per track + 2 unknown bytes.
        # 255 = no assignment (the Octatrack's "OFF" state).
        self._xlv_data = bytearray([SCENE_LOCK_DISABLED] * SCENE_XLV_SIZE)
        self._tracks: Dict[int, AudioSceneTrack] = {}

        # Apply provided tracks
        if tracks:
            for track in tracks:
                self.set_track(track.track_num, track)

    @classmethod
    def read(cls, scene_num: int, scene_data: bytes, xlv_data: Optional[bytes] = None) -> "Scene":
        """
        Read a Scene from binary data.

        Args:
            scene_num: Scene number (1-16)
            scene_data: SCENE_SIZE bytes of scene data
            xlv_data: Optional SCENE_XLV_SIZE bytes of crossfader assignment data

        Returns:
            Scene instance
        """
        instance = cls.__new__(cls)
        instance._scene_num = scene_num
        instance._data = bytearray(scene_data[:SCENE_SIZE])
        if xlv_data is None:
            instance._xlv_data = bytearray([SCENE_LOCK_DISABLED] * SCENE_XLV_SIZE)
        else:
            instance._xlv_data = bytearray(xlv_data[:SCENE_XLV_SIZE])
        instance._tracks = {}
        return instance

    def write(self) -> bytes:
        """
        Write this Scene to binary data.

        Syncs any modified tracks back to the buffer before returning.

        Returns:
            SCENE_SIZE bytes
        """
        # Sync any modified tracks back to buffer
        for track_num, track in self._tracks.items():
            self._sync_track_to_buffer(track_num, track)

        return bytes(self._data)

    def _sync_track_to_buffer(self, track_num: int, track: AudioSceneTrack):
        """Sync a track's data back to the scene buffer."""
        offset = (track_num - 1) * SCENE_PARAMS_SIZE
        self._data[offset:offset + SCENE_PARAMS_SIZE] = track.write()

    def clone(self) -> "Scene":
        """Create a copy of this Scene."""
        # First sync any modified tracks to buffer
        for track_num, track in self._tracks.items():
            self._sync_track_to_buffer(track_num, track)

        instance = Scene.__new__(Scene)
        instance._scene_num = self._scene_num
        instance._data = bytearray(self._data)
        instance._xlv_data = bytearray(self._xlv_data)
        instance._tracks = {}
        return instance

    def write_xlv(self) -> bytes:
        """Write this scene's crossfader (XLV) assignments to binary data.

        Returns SCENE_XLV_SIZE bytes — 8 per-track XLV values plus 2 unknown bytes.
        """
        return bytes(self._xlv_data)

    # === Crossfader (XLV) assignments ===

    def crossfader(self, track_num: int) -> Optional[int]:
        """
        Get the crossfader (XLV) assignment for `track_num` (1-8).

        Returns the lock value 0-127 (MIN..MAX) or None when no XLV
        assignment is set for this track in this scene.
        """
        if track_num < 1 or track_num > _SCENE_XLV_TRACK_COUNT:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        value = self._xlv_data[track_num - 1]
        return None if value == SCENE_LOCK_DISABLED else value

    def set_crossfader(self, track_num: int, value: Optional[int]):
        """
        Set the crossfader (XLV) assignment for `track_num` (1-8).

        Args:
            track_num: Audio track number (1-8)
            value: Lock value 0-127 (MIN..MAX), or None to clear.

        Pass None (or 255) to remove the assignment so the crossfader
        ignores the track for this scene.
        """
        if track_num < 1 or track_num > _SCENE_XLV_TRACK_COUNT:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        if value is None:
            self._xlv_data[track_num - 1] = SCENE_LOCK_DISABLED
            return
        if not 0 <= value <= 127:
            raise ValueError(f"Crossfader value must be 0-127 or None, got {value}")
        self._xlv_data[track_num - 1] = value & 0x7F

    @property
    def crossfader_assignments(self) -> Dict[int, int]:
        """Return a dict of {track_num: value} for tracks with an assignment."""
        result: Dict[int, int] = {}
        for i in range(_SCENE_XLV_TRACK_COUNT):
            v = self._xlv_data[i]
            if v != SCENE_LOCK_DISABLED:
                result[i + 1] = v
        return result

    # === Basic properties ===

    @property
    def scene_num(self) -> int:
        """Get the scene number (1-16)."""
        return self._scene_num

    # === Track access ===

    def track(self, track_num: int) -> AudioSceneTrack:
        """
        Get a track's scene locks (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioSceneTrack instance for this position
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")

        if track_num not in self._tracks:
            self._tracks[track_num] = self._load_track(track_num)

        return self._tracks[track_num]

    def _load_track(self, track_num: int) -> AudioSceneTrack:
        """Load a track from the buffer."""
        offset = (track_num - 1) * SCENE_PARAMS_SIZE
        track_data = bytes(self._data[offset:offset + SCENE_PARAMS_SIZE])
        return AudioSceneTrack.read(track_num, track_data)

    def set_track(self, track_num: int, track: AudioSceneTrack):
        """
        Set a track at the given position.

        Args:
            track_num: Track number (1-8)
            track: AudioSceneTrack to set
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")

        # Update track's internal track_num to match position
        track._track_num = track_num
        self._tracks[track_num] = track

    # === Utility methods ===

    def clear_all_locks(self):
        """Clear all locks for all tracks."""
        for i in range(SCENE_SIZE):
            self._data[i] = SCENE_LOCK_DISABLED
        # Clear cached tracks
        self._tracks.clear()

    @property
    def is_blank(self) -> bool:
        """Check if scene has no locks set on any track (param or XLV)."""
        # First check any loaded tracks
        for track in self._tracks.values():
            if track.has_locks():
                return False
        # Then check unloaded tracks in buffer
        for track_num in range(1, 9):
            if track_num not in self._tracks:
                offset = (track_num - 1) * SCENE_PARAMS_SIZE
                track_data = self._data[offset:offset + SCENE_PARAMS_SIZE]
                if any(b != SCENE_LOCK_DISABLED for b in track_data):
                    return False
        # Check crossfader (XLV) assignments
        for i in range(_SCENE_XLV_TRACK_COUNT):
            if self._xlv_data[i] != SCENE_LOCK_DISABLED:
                return False
        return True

    def has_locks(self) -> bool:
        """Check if scene has any locks set on any track."""
        return not self.is_blank

    # === Serialization ===

    def to_dict(self) -> dict:
        """
        Convert scene to dictionary.

        Returns dict with scene number and tracks that have any locks set.
        """
        result = {"scene": self._scene_num, "tracks": []}

        for track_num in range(1, 9):
            track = self.track(track_num)
            if track.has_locks():
                result["tracks"].append(track.to_dict())

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        """Create a Scene from a dictionary."""
        scene = cls(scene_num=data.get("scene", 1))

        if "tracks" in data:
            for track_data in data["tracks"]:
                track = AudioSceneTrack.from_dict(track_data)
                scene.set_track(track.track_num, track)

        return scene

    def __eq__(self, other) -> bool:
        """Check equality based on data buffer (param locks + XLV)."""
        if not isinstance(other, Scene):
            return NotImplemented
        return (
            self._scene_num == other._scene_num
            and self._data == other._data
            and self._xlv_data == other._xlv_data
        )

    def __repr__(self) -> str:
        tracks_with_locks = sum(1 for n in range(1, 9) if self.track(n).has_locks())
        return f"Scene(scene={self._scene_num}, tracks_with_locks={tracks_with_locks})"
