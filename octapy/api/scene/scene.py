"""
Scene class - container for scene track locks.
"""

from __future__ import annotations

from typing import Dict

from .audio import AudioSceneTrack
from .sampler import SamplerSceneTrack
from .thru import ThruSceneTrack
from .neighbor import NeighborSceneTrack
from .pickup import PickupSceneTrack


class Scene:
    """
    Pythonic interface for an Octatrack Scene.

    A Scene holds parameter locks for crossfader morphing across all 8 audio tracks.
    Each Part has 16 scenes.

    Usage:
        scene = part.scene(1)

        # Generic track access (base AudioSceneTrack)
        track = scene.track(1)
        track.amp_volume = 100

        # Machine-specific access with typed properties
        sampler = scene.sampler_track(1)
        sampler.pitch = 72
        sampler.start = 0
    """

    def __init__(self, part: Part, scene_num: int):
        self._part = part
        self._scene_num = scene_num
        self._tracks: Dict[int, AudioSceneTrack] = {}
        self._sampler_tracks: Dict[int, SamplerSceneTrack] = {}
        self._thru_tracks: Dict[int, ThruSceneTrack] = {}
        self._neighbor_tracks: Dict[int, NeighborSceneTrack] = {}
        self._pickup_tracks: Dict[int, PickupSceneTrack] = {}

    def track(self, track_num: int) -> AudioSceneTrack:
        """
        Get a track (1-8) as base AudioSceneTrack.

        For machine-specific playback locks, use sampler_track(), thru_track(), etc.

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioSceneTrack instance for configuring AMP/FX locks
        """
        if track_num not in self._tracks:
            self._tracks[track_num] = AudioSceneTrack(self, track_num)
        return self._tracks[track_num]

    def sampler_track(self, track_num: int) -> SamplerSceneTrack:
        """
        Get a track (1-8) as SamplerSceneTrack with Flex/Static playback locks.

        Args:
            track_num: Track number (1-8)

        Returns:
            SamplerSceneTrack instance with pitch, start, length, rate, etc.
        """
        if track_num not in self._sampler_tracks:
            self._sampler_tracks[track_num] = SamplerSceneTrack(self, track_num)
        return self._sampler_tracks[track_num]

    def thru_track(self, track_num: int) -> ThruSceneTrack:
        """
        Get a track (1-8) as ThruSceneTrack with Thru playback locks.

        Args:
            track_num: Track number (1-8)

        Returns:
            ThruSceneTrack instance with in_ab, vol_ab, in_cd, vol_cd
        """
        if track_num not in self._thru_tracks:
            self._thru_tracks[track_num] = ThruSceneTrack(self, track_num)
        return self._thru_tracks[track_num]

    def neighbor_track(self, track_num: int) -> NeighborSceneTrack:
        """
        Get a track (1-8) as NeighborSceneTrack.

        Neighbor machines have no machine-specific playback parameters,
        but AMP/FX locks are available.

        Args:
            track_num: Track number (1-8)

        Returns:
            NeighborSceneTrack instance with AMP/FX locks
        """
        if track_num not in self._neighbor_tracks:
            self._neighbor_tracks[track_num] = NeighborSceneTrack(self, track_num)
        return self._neighbor_tracks[track_num]

    def pickup_track(self, track_num: int) -> PickupSceneTrack:
        """
        Get a track (1-8) as PickupSceneTrack with Pickup playback locks.

        Args:
            track_num: Track number (1-8)

        Returns:
            PickupSceneTrack instance with pitch, direction, gain, operation
        """
        if track_num not in self._pickup_tracks:
            self._pickup_tracks[track_num] = PickupSceneTrack(self, track_num)
        return self._pickup_tracks[track_num]

    def clear_all_locks(self):
        """Clear all locks for all tracks in this scene."""
        for track_num in range(1, 9):
            self.track(track_num).clear_all_locks()
