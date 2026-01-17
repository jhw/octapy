"""
Part class - container for track configurations.
"""

from __future__ import annotations

from typing import Dict

from ..._io import PartOffset
from .audio import AudioPartTrack
from .flex import FlexPartTrack
from .static import StaticPartTrack
from .thru import ThruPartTrack
from .neighbor import NeighborPartTrack
from .pickup import PickupPartTrack
from .midi import MidiPartTrack


class Part:
    """
    Pythonic interface for an Octatrack Part.

    A Part holds machine configurations for all 8 tracks.
    Each bank has 4 parts.

    Usage:
        part = bank.part(1)

        # Generic track access (base AudioPartTrack)
        track = part.track(1)
        track.machine_type = MachineType.FLEX

        # Machine-specific access with typed properties
        flex = part.flex_track(1)
        flex.pitch = 64
        flex.timestretch = 0
    """

    def __init__(self, bank: "Bank", part_num: int):
        self._bank = bank
        self._part_num = part_num
        self._tracks: Dict[int, AudioPartTrack] = {}
        self._flex_tracks: Dict[int, FlexPartTrack] = {}
        self._static_tracks: Dict[int, StaticPartTrack] = {}
        self._thru_tracks: Dict[int, ThruPartTrack] = {}
        self._neighbor_tracks: Dict[int, NeighborPartTrack] = {}
        self._pickup_tracks: Dict[int, PickupPartTrack] = {}
        self._midi_tracks: Dict[int, MidiPartTrack] = {}

    def _part_offset(self) -> int:
        """Get the byte offset for this part in the bank file."""
        return self._bank._bank_file.part_offset(self._part_num)

    def track(self, track_num: int) -> AudioPartTrack:
        """
        Get a track (1-8) as base AudioPartTrack.

        For machine-specific parameters, use flex_track(), static_track(), etc.

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioPartTrack instance for configuring machine settings
        """
        if track_num not in self._tracks:
            self._tracks[track_num] = AudioPartTrack(self, track_num)
        return self._tracks[track_num]

    def flex_track(self, track_num: int) -> FlexPartTrack:
        """
        Get a track (1-8) as FlexPartTrack with Flex-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            FlexPartTrack instance with pitch, start, length, rate, etc.
        """
        if track_num not in self._flex_tracks:
            self._flex_tracks[track_num] = FlexPartTrack(self, track_num)
        return self._flex_tracks[track_num]

    def static_track(self, track_num: int) -> StaticPartTrack:
        """
        Get a track (1-8) as StaticPartTrack with Static-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            StaticPartTrack instance with pitch, start, length, rate, etc.
        """
        if track_num not in self._static_tracks:
            self._static_tracks[track_num] = StaticPartTrack(self, track_num)
        return self._static_tracks[track_num]

    def thru_track(self, track_num: int) -> ThruPartTrack:
        """
        Get a track (1-8) as ThruPartTrack with Thru-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            ThruPartTrack instance with in_ab, vol_ab, in_cd, vol_cd
        """
        if track_num not in self._thru_tracks:
            self._thru_tracks[track_num] = ThruPartTrack(self, track_num)
        return self._thru_tracks[track_num]

    def neighbor_track(self, track_num: int) -> NeighborPartTrack:
        """
        Get a track (1-8) as NeighborPartTrack.

        Neighbor machines have no machine-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            NeighborPartTrack instance
        """
        if track_num not in self._neighbor_tracks:
            self._neighbor_tracks[track_num] = NeighborPartTrack(self, track_num)
        return self._neighbor_tracks[track_num]

    def pickup_track(self, track_num: int) -> PickupPartTrack:
        """
        Get a track (1-8) as PickupPartTrack with Pickup-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            PickupPartTrack instance with pitch, direction, gain, operation, etc.
        """
        if track_num not in self._pickup_tracks:
            self._pickup_tracks[track_num] = PickupPartTrack(self, track_num)
        return self._pickup_tracks[track_num]

    def midi_track(self, track_num: int) -> MidiPartTrack:
        """
        Get MIDI configuration for a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPartTrack instance for configuring MIDI settings
        """
        if track_num not in self._midi_tracks:
            self._midi_tracks[track_num] = MidiPartTrack(self, track_num)
        return self._midi_tracks[track_num]

    @property
    def active_scene_a(self) -> int:
        """Get/set active scene A (0-15)."""
        data = self._bank._bank_file._data
        return data[self._part_offset() + PartOffset.ACTIVE_SCENE_A]

    @active_scene_a.setter
    def active_scene_a(self, value: int):
        data = self._bank._bank_file._data
        data[self._part_offset() + PartOffset.ACTIVE_SCENE_A] = value & 0x0F

    @property
    def active_scene_b(self) -> int:
        """Get/set active scene B (0-15)."""
        data = self._bank._bank_file._data
        return data[self._part_offset() + PartOffset.ACTIVE_SCENE_B]

    @active_scene_b.setter
    def active_scene_b(self, value: int):
        data = self._bank._bank_file._data
        data[self._part_offset() + PartOffset.ACTIVE_SCENE_B] = value & 0x0F
