"""
Track layout management for Part configurations.

Provides different track layout configurations:
- EIGHT_TRACK: Standard 8 tracks (default)
- SEVEN_PLUS_MASTER: 7 content tracks + master on track 8
- FOUR_PLUS_NEIGHBOR: 4 content tracks with neighbor routing for extra FX
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .part import Part
    from .audio import AudioPartTrack
    from .flex import FlexPartTrack
    from .static import StaticPartTrack
    from .thru import ThruPartTrack
    from .neighbor import NeighborPartTrack
    from .midi import MidiPartTrack


class TrackLayout(Enum):
    """
    Track layout configurations for audio tracks.

    EIGHT_TRACK: Standard 8 tracks, no special routing
    SEVEN_PLUS_MASTER: Tracks 1-7 for content, track 8 reserved for master
    FOUR_PLUS_NEIGHBOR: 4 content tracks with neighbor routing for fx3/fx4
    """
    EIGHT_TRACK = "eight_track"
    SEVEN_PLUS_MASTER = "seven_plus_master"
    FOUR_PLUS_NEIGHBOR = "four_plus_neighbor"


class AudioPartTrackManager:
    """
    Manages audio track access with layout-specific behavior.

    Provides a consistent track(n) interface while supporting different
    physical track mappings based on the selected layout.

    Layouts:
        EIGHT_TRACK: Direct mapping, tracks 1-8 -> physical 1-8
        SEVEN_PLUS_MASTER: Tracks 1-7 for content, track 8 is master
        FOUR_PLUS_NEIGHBOR: Tracks 1-4 map to physical 1,3,5,7
                           Neighbors on physical 2,4,6,8
                           Supports fx3/fx4 via neighbor's fx1/fx2

    Usage:
        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER
        track = part.audio_tracks.track(1)  # Physical track 1
        track.fx1_type = FX1Type.FILTER

        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR
        track = part.audio_tracks.track(2)  # Physical track 3
        track.fx3_type = FX1Type.COMPRESSOR  # Goes to neighbor (physical 4)
    """

    # Logical -> Physical track mapping for FOUR_PLUS_NEIGHBOR
    FOUR_PLUS_NEIGHBOR_MAP = {1: 1, 2: 3, 3: 5, 4: 7}
    # Physical neighbor track positions
    NEIGHBOR_TRACKS = {1: 2, 3: 4, 5: 6, 7: 8}

    def __init__(self, part: Part):
        self._part = part
        self._layout = TrackLayout.EIGHT_TRACK

    @property
    def layout(self) -> TrackLayout:
        """Get/set the current track layout."""
        return self._layout

    @layout.setter
    def layout(self, value: TrackLayout):
        self._layout = value

    @property
    def max_tracks(self) -> int:
        """Maximum number of logical tracks for current layout."""
        if self._layout == TrackLayout.EIGHT_TRACK:
            return 8
        elif self._layout == TrackLayout.SEVEN_PLUS_MASTER:
            return 7
        elif self._layout == TrackLayout.FOUR_PLUS_NEIGHBOR:
            return 4
        return 8

    def _logical_to_physical(self, logical_num: int) -> int:
        """Convert logical track number to physical track number."""
        if self._layout == TrackLayout.FOUR_PLUS_NEIGHBOR:
            if logical_num not in self.FOUR_PLUS_NEIGHBOR_MAP:
                raise ValueError(
                    f"Track {logical_num} invalid for FOUR_PLUS_NEIGHBOR layout. "
                    f"Valid tracks: 1-4"
                )
            return self.FOUR_PLUS_NEIGHBOR_MAP[logical_num]
        else:
            # EIGHT_TRACK and SEVEN_PLUS_MASTER use direct mapping
            return logical_num

    def _validate_track_num(self, track_num: int) -> None:
        """Validate track number for current layout."""
        if track_num < 1 or track_num > self.max_tracks:
            raise ValueError(
                f"Track {track_num} out of range for {self._layout.name} layout. "
                f"Valid tracks: 1-{self.max_tracks}"
            )

    def track(self, track_num: int) -> AudioPartTrack:
        """
        Get a track as base AudioPartTrack.

        Args:
            track_num: Logical track number (depends on layout)

        Returns:
            AudioPartTrack instance
        """
        self._validate_track_num(track_num)
        physical = self._logical_to_physical(track_num)
        return self._part.track(physical)

    def flex_track(self, track_num: int) -> FlexPartTrack:
        """
        Get a track as FlexPartTrack.

        Args:
            track_num: Logical track number (depends on layout)

        Returns:
            FlexPartTrack instance
        """
        self._validate_track_num(track_num)
        physical = self._logical_to_physical(track_num)
        return self._part.flex_track(physical)

    def static_track(self, track_num: int) -> StaticPartTrack:
        """
        Get a track as StaticPartTrack.

        Args:
            track_num: Logical track number (depends on layout)

        Returns:
            StaticPartTrack instance
        """
        self._validate_track_num(track_num)
        physical = self._logical_to_physical(track_num)
        return self._part.static_track(physical)

    def thru_track(self, track_num: int) -> ThruPartTrack:
        """
        Get a track as ThruPartTrack.

        Args:
            track_num: Logical track number (depends on layout)

        Returns:
            ThruPartTrack instance
        """
        self._validate_track_num(track_num)
        physical = self._logical_to_physical(track_num)
        return self._part.thru_track(physical)

    def neighbor_track(self, track_num: int) -> Optional[NeighborPartTrack]:
        """
        Get the neighbor track for a given logical track.

        Only valid for FOUR_PLUS_NEIGHBOR layout.

        Args:
            track_num: Logical track number (1-4)

        Returns:
            NeighborPartTrack instance, or None if not FOUR_PLUS_NEIGHBOR layout
        """
        if self._layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            return None
        self._validate_track_num(track_num)
        physical = self._logical_to_physical(track_num)
        neighbor_physical = self.NEIGHBOR_TRACKS[physical]
        return self._part.neighbor_track(neighbor_physical)

    def __iter__(self):
        """Iterate over all logical tracks."""
        for i in range(1, self.max_tracks + 1):
            yield self.track(i)


class LayoutAwareTrack:
    """
    Wrapper that provides fx3/fx4 access for FOUR_PLUS_NEIGHBOR layout.

    This wraps an AudioPartTrack and adds fx3/fx4 properties that
    transparently access the neighbor track's fx1/fx2.
    """

    def __init__(self, manager: AudioPartTrackManager, logical_track: int):
        self._manager = manager
        self._logical_track = logical_track
        self._track = manager.track(logical_track)

    def __getattr__(self, name):
        """Delegate to underlying track."""
        return getattr(self._track, name)

    @property
    def fx3_type(self) -> int:
        """
        Get/set FX3 type (neighbor's FX1).

        Only valid for FOUR_PLUS_NEIGHBOR layout.
        """
        if self._manager.layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            raise AttributeError("fx3_type only available in FOUR_PLUS_NEIGHBOR layout")
        neighbor = self._manager.neighbor_track(self._logical_track)
        return neighbor.fx1_type

    @fx3_type.setter
    def fx3_type(self, value: int):
        if self._manager.layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            raise AttributeError("fx3_type only available in FOUR_PLUS_NEIGHBOR layout")
        neighbor = self._manager.neighbor_track(self._logical_track)
        neighbor.fx1_type = value

    @property
    def fx4_type(self) -> int:
        """
        Get/set FX4 type (neighbor's FX2).

        Only valid for FOUR_PLUS_NEIGHBOR layout.
        """
        if self._manager.layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            raise AttributeError("fx4_type only available in FOUR_PLUS_NEIGHBOR layout")
        neighbor = self._manager.neighbor_track(self._logical_track)
        return neighbor.fx2_type

    @fx4_type.setter
    def fx4_type(self, value: int):
        if self._manager.layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            raise AttributeError("fx4_type only available in FOUR_PLUS_NEIGHBOR layout")
        neighbor = self._manager.neighbor_track(self._logical_track)
        neighbor.fx2_type = value

    @property
    def fx3(self):
        """
        Get FX3 container (neighbor's FX1).

        Only valid for FOUR_PLUS_NEIGHBOR layout.
        """
        if self._manager.layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            raise AttributeError("fx3 only available in FOUR_PLUS_NEIGHBOR layout")
        neighbor = self._manager.neighbor_track(self._logical_track)
        return neighbor.fx1

    @property
    def fx4(self):
        """
        Get FX4 container (neighbor's FX2).

        Only valid for FOUR_PLUS_NEIGHBOR layout.
        """
        if self._manager.layout != TrackLayout.FOUR_PLUS_NEIGHBOR:
            raise AttributeError("fx4 only available in FOUR_PLUS_NEIGHBOR layout")
        neighbor = self._manager.neighbor_track(self._logical_track)
        return neighbor.fx2


class MidiPartTrackManager:
    """
    Manages MIDI track access.

    MIDI tracks don't support layouts - this is a passthrough manager
    that provides a consistent interface matching AudioPartTrackManager.
    """

    def __init__(self, part: Part):
        self._part = part

    @property
    def max_tracks(self) -> int:
        """Maximum number of MIDI tracks (always 8)."""
        return 8

    def track(self, track_num: int) -> MidiPartTrack:
        """
        Get a MIDI track.

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPartTrack instance
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"MIDI track {track_num} out of range. Valid tracks: 1-8")
        return self._part.midi_track(track_num)

    def __iter__(self):
        """Iterate over all MIDI tracks."""
        for i in range(1, 9):
            yield self.track(i)
