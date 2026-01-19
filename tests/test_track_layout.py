"""
Tests for track layout management.
"""

import pytest

from octapy import Project, MachineType, TrackLayout


class TestTrackLayout:
    """Tests for TrackLayout enum and basic behavior."""

    def test_layout_enum_values(self):
        """TrackLayout enum has expected values."""
        assert TrackLayout.EIGHT_TRACK.value == "eight_track"
        assert TrackLayout.SEVEN_PLUS_MASTER.value == "seven_plus_master"
        assert TrackLayout.FOUR_PLUS_NEIGHBOR.value == "four_plus_neighbor"

    def test_default_layout_is_eight_track(self):
        """Default layout is EIGHT_TRACK."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        assert part.audio_tracks.layout == TrackLayout.EIGHT_TRACK

    def test_layout_can_be_changed(self):
        """Layout can be changed to other values."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER
        assert part.audio_tracks.layout == TrackLayout.SEVEN_PLUS_MASTER

        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR
        assert part.audio_tracks.layout == TrackLayout.FOUR_PLUS_NEIGHBOR


class TestEightTrackLayout:
    """Tests for EIGHT_TRACK layout (default)."""

    def test_max_tracks_is_8(self):
        """EIGHT_TRACK layout has 8 tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.EIGHT_TRACK
        assert part.audio_tracks.max_tracks == 8

    def test_all_tracks_accessible(self):
        """All 8 tracks are accessible."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        for i in range(1, 9):
            track = part.audio_tracks.track(i)
            assert track is not None

    def test_track_out_of_range_raises(self):
        """Track 9 raises ValueError."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        with pytest.raises(ValueError, match="out of range"):
            part.audio_tracks.track(9)

    def test_direct_mapping(self):
        """Logical tracks map directly to physical tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        # Set machine type via manager
        part.audio_tracks.track(3).machine_type = MachineType.FLEX

        # Should be the same as direct part access
        assert part.track(3).machine_type == MachineType.FLEX


class TestSevenPlusMasterLayout:
    """Tests for SEVEN_PLUS_MASTER layout."""

    def test_max_tracks_is_7(self):
        """SEVEN_PLUS_MASTER layout has 7 content tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER
        assert part.audio_tracks.max_tracks == 7

    def test_tracks_1_to_7_accessible(self):
        """Tracks 1-7 are accessible."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER

        for i in range(1, 8):
            track = part.audio_tracks.track(i)
            assert track is not None

    def test_track_8_raises(self):
        """Track 8 raises ValueError in SEVEN_PLUS_MASTER."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER

        with pytest.raises(ValueError, match="out of range"):
            part.audio_tracks.track(8)

    def test_direct_mapping_for_tracks_1_to_7(self):
        """Tracks 1-7 map directly to physical tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER

        part.audio_tracks.track(5).machine_type = MachineType.STATIC
        assert part.track(5).machine_type == MachineType.STATIC


class TestFourPlusNeighborLayout:
    """Tests for FOUR_PLUS_NEIGHBOR layout."""

    def test_max_tracks_is_4(self):
        """FOUR_PLUS_NEIGHBOR layout has 4 content tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR
        assert part.audio_tracks.max_tracks == 4

    def test_tracks_1_to_4_accessible(self):
        """Tracks 1-4 are accessible."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR

        for i in range(1, 5):
            track = part.audio_tracks.track(i)
            assert track is not None

    def test_track_5_raises(self):
        """Track 5 raises ValueError in FOUR_PLUS_NEIGHBOR."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR

        with pytest.raises(ValueError, match="out of range"):
            part.audio_tracks.track(5)

    def test_logical_to_physical_mapping(self):
        """Logical tracks map to correct physical tracks: 1->1, 2->3, 3->5, 4->7."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR

        # Logical 1 -> Physical 1
        part.audio_tracks.track(1).machine_type = MachineType.FLEX
        assert part.track(1).machine_type == MachineType.FLEX

        # Logical 2 -> Physical 3
        part.audio_tracks.track(2).machine_type = MachineType.STATIC
        assert part.track(3).machine_type == MachineType.STATIC

        # Logical 3 -> Physical 5
        part.audio_tracks.track(3).machine_type = MachineType.THRU
        assert part.track(5).machine_type == MachineType.THRU

        # Logical 4 -> Physical 7
        part.audio_tracks.track(4).machine_type = MachineType.NEIGHBOR
        assert part.track(7).machine_type == MachineType.NEIGHBOR

    def test_neighbor_track_access(self):
        """Neighbor tracks are accessible and map to correct physical tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR

        # Neighbor for logical 1 is physical 2
        neighbor1 = part.audio_tracks.neighbor_track(1)
        assert neighbor1 is not None

        # Verify it's physical track 2
        neighbor1.machine_type = MachineType.NEIGHBOR
        assert part.track(2).machine_type == MachineType.NEIGHBOR

        # Neighbor for logical 2 is physical 4
        neighbor2 = part.audio_tracks.neighbor_track(2)
        neighbor2.machine_type = MachineType.NEIGHBOR
        assert part.track(4).machine_type == MachineType.NEIGHBOR

        # Neighbor for logical 3 is physical 6
        neighbor3 = part.audio_tracks.neighbor_track(3)
        neighbor3.machine_type = MachineType.NEIGHBOR
        assert part.track(6).machine_type == MachineType.NEIGHBOR

        # Neighbor for logical 4 is physical 8
        neighbor4 = part.audio_tracks.neighbor_track(4)
        neighbor4.machine_type = MachineType.NEIGHBOR
        assert part.track(8).machine_type == MachineType.NEIGHBOR

    def test_neighbor_track_returns_none_for_other_layouts(self):
        """neighbor_track returns None for non-FOUR_PLUS_NEIGHBOR layouts."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        part.audio_tracks.layout = TrackLayout.EIGHT_TRACK
        assert part.audio_tracks.neighbor_track(1) is None

        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER
        assert part.audio_tracks.neighbor_track(1) is None


class TestFlexTrackAccess:
    """Tests for flex_track access via layout manager."""

    def test_flex_track_respects_layout(self):
        """flex_track respects the current layout."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR

        # Logical 2 -> Physical 3
        flex = part.audio_tracks.flex_track(2)
        flex.pitch = 72

        # Should have set physical track 3
        assert part.flex_track(3).pitch == 72


class TestMidiPartTrackManager:
    """Tests for MidiPartTrackManager."""

    def test_midi_max_tracks_is_8(self):
        """MIDI track manager always has 8 tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        assert part.midi_tracks.max_tracks == 8

    def test_midi_tracks_accessible(self):
        """All MIDI tracks are accessible."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        for i in range(1, 9):
            track = part.midi_tracks.track(i)
            assert track is not None

    def test_midi_track_out_of_range_raises(self):
        """MIDI track 9 raises ValueError."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        with pytest.raises(ValueError, match="out of range"):
            part.midi_tracks.track(9)


class TestIterator:
    """Tests for track iterator behavior."""

    def test_audio_tracks_iterator(self):
        """Can iterate over audio tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        tracks = list(part.audio_tracks)
        assert len(tracks) == 8

    def test_seven_plus_master_iterator(self):
        """Iterator respects SEVEN_PLUS_MASTER layout."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.SEVEN_PLUS_MASTER

        tracks = list(part.audio_tracks)
        assert len(tracks) == 7

    def test_four_plus_neighbor_iterator(self):
        """Iterator respects FOUR_PLUS_NEIGHBOR layout."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.audio_tracks.layout = TrackLayout.FOUR_PLUS_NEIGHBOR

        tracks = list(part.audio_tracks)
        assert len(tracks) == 4

    def test_midi_tracks_iterator(self):
        """Can iterate over MIDI tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        tracks = list(part.midi_tracks)
        assert len(tracks) == 8
