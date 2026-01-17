"""
Tests for Part and AudioPartTrack high-level API.
"""

import pytest

from octapy import Project, MachineType


class TestPartBasics:
    """Basic Part tests via high-level API."""

    def test_get_part(self):
        """Test getting a Part from a Bank."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        assert part is not None

    def test_get_all_parts(self):
        """Test getting all 4 parts."""
        project = Project.from_template("TEST")
        for i in range(1, 5):
            part = project.bank(1).part(i)
            assert part is not None


class TestAudioPartTrackMachineTypes:
    """AudioPartTrack machine type tests."""

    def test_default_machine_type(self):
        """Test default machine type is STATIC."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            track = part.track(track_num)
            assert track.machine_type == MachineType.STATIC

    def test_set_machine_type(self):
        """Test setting machine type."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.machine_type = MachineType.FLEX
        assert track.machine_type == MachineType.FLEX

    def test_set_all_machine_types(self):
        """Test setting machine types on all tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        types = [
            MachineType.FLEX,
            MachineType.STATIC,
            MachineType.THRU,
            MachineType.NEIGHBOR,
            MachineType.PICKUP,
            MachineType.FLEX,
            MachineType.STATIC,
            MachineType.THRU,
        ]

        for track_num, machine_type in enumerate(types, 1):
            part.track(track_num).machine_type = machine_type

        for track_num, expected in enumerate(types, 1):
            assert part.track(track_num).machine_type == expected


class TestAudioPartTrackVolumes:
    """AudioPartTrack volume tests."""

    def test_default_volume(self):
        """Test default volume is 108."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            track = part.track(track_num)
            main, cue = track.volume
            assert main == 108
            assert cue == 108

    def test_set_volume(self):
        """Test setting volume."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.set_volume(main=100, cue=50)

        main, cue = track.volume
        assert main == 100
        assert cue == 50

    def test_volume_clamping(self):
        """Test volume values are clamped to 7 bits."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.set_volume(main=200, cue=200)  # Over 127

        main, cue = track.volume
        assert main <= 127
        assert cue <= 127


class TestAudioPartTrackFX:
    """AudioPartTrack FX tests."""

    def test_default_fx1(self):
        """Test default FX1 is Filter (4)."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            assert part.track(track_num).fx1_type == 4

    def test_default_fx2(self):
        """Test default FX2 is Delay (8)."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            assert part.track(track_num).fx2_type == 8

    def test_set_fx_types(self):
        """Test setting FX types."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.fx1_type = 12  # EQ
        track.fx2_type = 20  # Plate Reverb

        assert track.fx1_type == 12
        assert track.fx2_type == 20


class TestPartScenes:
    """Part scene tests."""

    def test_default_scenes(self):
        """Test default active scenes."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        assert part.active_scene_a == 0
        assert part.active_scene_b == 8

    def test_set_scenes(self):
        """Test setting active scenes."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.active_scene_a = 5
        part.active_scene_b = 12

        assert part.active_scene_a == 5
        assert part.active_scene_b == 12

    def test_scene_clamping(self):
        """Test scene values are clamped to 4 bits."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.active_scene_a = 20  # Over 15
        part.active_scene_b = 20

        assert part.active_scene_a <= 15
        assert part.active_scene_b <= 15


class TestAudioPartTrackSlots:
    """AudioPartTrack slot assignment tests."""

    def test_set_flex_slot(self):
        """Test setting flex slot."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.flex_slot = 5
        assert track.flex_slot == 5

    def test_set_static_slot(self):
        """Test setting static slot."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.static_slot = 10
        assert track.static_slot == 10

    def test_set_recorder_slot(self):
        """Test setting recorder slot."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.recorder_slot = 129
        assert track.recorder_slot == 129

    def test_all_slot_types(self):
        """Test all slot types on one track."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)

        track.static_slot = 1
        track.flex_slot = 2
        track.recorder_slot = 129

        assert track.static_slot == 1
        assert track.flex_slot == 2
        assert track.recorder_slot == 129


class TestMidiPartTrackBasics:
    """MidiPartTrack basic tests."""

    def test_get_midi_track(self):
        """Test getting a MIDI track from a Part."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track is not None

    def test_get_all_midi_tracks(self):
        """Test getting all 8 MIDI tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for i in range(1, 9):
            midi_track = part.midi_track(i)
            assert midi_track is not None


class TestMidiPartTrackChannel:
    """MidiPartTrack channel tests."""

    def test_default_channel(self):
        """Test default MIDI channel is 0."""
        project = Project.from_template("TEST")
        for track_num in range(1, 9):
            midi_track = project.bank(1).part(1).midi_track(track_num)
            assert midi_track.channel == 0

    def test_set_channel(self):
        """Test setting MIDI channel."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.channel = 5
        assert midi_track.channel == 5

    def test_channel_clamping(self):
        """Test channel values are clamped to 4 bits (0-15)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.channel = 20  # Over 15
        assert midi_track.channel <= 15


class TestMidiPartTrackProgram:
    """MidiPartTrack bank/program tests."""

    def test_default_bank(self):
        """Test default bank is 128 (off)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.bank == 128

    def test_default_program(self):
        """Test default program is 128 (off)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.program == 128

    def test_set_bank(self):
        """Test setting bank select."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.bank = 10
        assert midi_track.bank == 10

    def test_set_program(self):
        """Test setting program change."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.program = 32
        assert midi_track.program == 32


class TestMidiPartTrackDefaults:
    """MidiPartTrack default note/velocity/length tests."""

    def test_default_note(self):
        """Test default note is 48 (C3)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_note == 48

    def test_default_velocity(self):
        """Test default velocity is 100."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_velocity == 100

    def test_default_length(self):
        """Test default length is 6 (1/16)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_length == 6

    def test_set_default_note(self):
        """Test setting default note."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note = 60  # Middle C
        assert midi_track.default_note == 60

    def test_set_default_velocity(self):
        """Test setting default velocity."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_velocity = 127
        assert midi_track.default_velocity == 127

    def test_set_default_length(self):
        """Test setting default length."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_length = 12
        assert midi_track.default_length == 12


class TestMidiPartTrackCCNumbers:
    """MidiPartTrack CC number assignment tests."""

    def test_default_cc_numbers(self):
        """Test default CC numbers from template."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        # Template defaults: 7(Vol), 1(Mod), 2(Breath), 10(Pan), 71-76(Sound)
        expected = [7, 1, 2, 10, 71, 72, 73, 74, 75, 76]
        for i, exp in enumerate(expected, 1):
            assert midi_track.cc_number(i) == exp, f"CC{i} number mismatch"

    def test_set_cc_number(self):
        """Test setting CC number."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.set_cc_number(1, 74)  # Filter cutoff
        assert midi_track.cc_number(1) == 74

    def test_set_all_cc_numbers(self):
        """Test setting all 10 CC numbers."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        # Set different CC numbers
        cc_values = [1, 7, 10, 11, 71, 74, 91, 93, 16, 17]
        for i, val in enumerate(cc_values, 1):
            midi_track.set_cc_number(i, val)

        # Verify
        for i, expected in enumerate(cc_values, 1):
            assert midi_track.cc_number(i) == expected, f"CC{i} mismatch"

    def test_cc_number_invalid_slot(self):
        """Test invalid CC slot raises ValueError."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        with pytest.raises(ValueError):
            midi_track.cc_number(0)
        with pytest.raises(ValueError):
            midi_track.cc_number(11)


class TestMidiPartTrackCCValues:
    """MidiPartTrack CC default value tests."""

    def test_default_pitch_bend(self):
        """Test default pitch bend is 64 (center)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.pitch_bend == 64

    def test_default_aftertouch(self):
        """Test default aftertouch is 0."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.aftertouch == 0

    def test_default_cc_values(self):
        """Test default CC values from template."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        # Template defaults: cc1(127)=Vol max, cc4(64)=Pan center, rest 0
        expected = [127, 0, 0, 64, 0, 0, 0, 0, 0, 0]
        for i, exp in enumerate(expected, 1):
            assert midi_track.cc_value(i) == exp, f"CC{i} value mismatch"

    def test_set_pitch_bend(self):
        """Test setting pitch bend."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.pitch_bend = 127  # Max up
        assert midi_track.pitch_bend == 127

    def test_set_aftertouch(self):
        """Test setting aftertouch."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.aftertouch = 100
        assert midi_track.aftertouch == 100

    def test_set_cc_values(self):
        """Test setting CC values."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        for i in range(1, 11):
            midi_track.set_cc_value(i, i * 10)

        for i in range(1, 11):
            assert midi_track.cc_value(i) == i * 10


class TestMidiPartTrackRoundTrip:
    """MidiPartTrack roundtrip tests."""

    def test_channel_roundtrip(self, temp_dir):
        """Test channel survives save/load."""
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).channel = 5
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        assert loaded.bank(1).part(1).midi_track(1).channel == 5

    def test_program_roundtrip(self, temp_dir):
        """Test program survives save/load."""
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).program = 64
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        assert loaded.bank(1).part(1).midi_track(1).program == 64

    def test_defaults_roundtrip(self, temp_dir):
        """Test default note/velocity/length survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note = 60
        midi_track.default_velocity = 110
        midi_track.default_length = 12
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_midi = loaded.bank(1).part(1).midi_track(1)
        assert loaded_midi.default_note == 60
        assert loaded_midi.default_velocity == 110
        assert loaded_midi.default_length == 12

    def test_all_tracks_roundtrip(self, temp_dir):
        """Test all 8 MIDI tracks survive save/load."""
        project = Project.from_template("TEST")
        for track_num in range(1, 9):
            midi_track = project.bank(1).part(1).midi_track(track_num)
            midi_track.channel = track_num - 1
            midi_track.default_note = 48 + track_num
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        for track_num in range(1, 9):
            midi_track = loaded.bank(1).part(1).midi_track(track_num)
            assert midi_track.channel == track_num - 1
            assert midi_track.default_note == 48 + track_num

    def test_cc_numbers_roundtrip(self, temp_dir):
        """Test CC numbers survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.set_cc_number(1, 74)
        midi_track.set_cc_number(2, 71)
        midi_track.set_cc_number(3, 91)
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_midi = loaded.bank(1).part(1).midi_track(1)
        assert loaded_midi.cc_number(1) == 74
        assert loaded_midi.cc_number(2) == 71
        assert loaded_midi.cc_number(3) == 91

    def test_cc_values_roundtrip(self, temp_dir):
        """Test CC values survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.pitch_bend = 100
        midi_track.aftertouch = 50
        midi_track.set_cc_value(1, 64)
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_midi = loaded.bank(1).part(1).midi_track(1)
        assert loaded_midi.pitch_bend == 100
        assert loaded_midi.aftertouch == 50
        assert loaded_midi.cc_value(1) == 64
