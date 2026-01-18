"""
Tests for Part and AudioPartTrack high-level API.
"""

import pytest

from octapy import Project, MachineType, NoteLength
from octapy.api.enums import MidiNote
from octapy.api.utils import quantize_note_length


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


class TestNoteLengthEnum:
    """NoteLength enum tests."""

    def test_enum_values(self):
        """Test NoteLength enum has correct MIDI tick values."""
        assert NoteLength.THIRTY_SECOND == 3
        assert NoteLength.SIXTEENTH == 6
        assert NoteLength.EIGHTH == 12
        assert NoteLength.QUARTER == 24
        assert NoteLength.HALF == 48

    def test_enum_as_int(self):
        """Test NoteLength values work as integers."""
        assert int(NoteLength.SIXTEENTH) == 6
        assert NoteLength.QUARTER * 2 == 48


class TestMidiNoteEnum:
    """MidiNote enum tests."""

    def test_octave_minus1_notes(self):
        """Test octave -1 note values (0-11)."""
        assert MidiNote.C_MINUS1 == 0
        assert MidiNote.Cs_MINUS1 == 1
        assert MidiNote.D_MINUS1 == 2
        assert MidiNote.E_MINUS1 == 4
        assert MidiNote.F_MINUS1 == 5
        assert MidiNote.G_MINUS1 == 7
        assert MidiNote.A_MINUS1 == 9
        assert MidiNote.B_MINUS1 == 11

    def test_octave_boundaries(self):
        """Test C notes at octave boundaries."""
        assert MidiNote.C_MINUS1 == 0
        assert MidiNote.C0 == 12
        assert MidiNote.C1 == 24
        assert MidiNote.C2 == 36
        assert MidiNote.C3 == 48
        assert MidiNote.C4 == 60   # Middle C
        assert MidiNote.C5 == 72
        assert MidiNote.C6 == 84
        assert MidiNote.C7 == 96
        assert MidiNote.C8 == 108
        assert MidiNote.C9 == 120

    def test_middle_c(self):
        """Test Middle C is 60."""
        assert MidiNote.C4 == 60

    def test_concert_a(self):
        """Test concert pitch A4 is 69."""
        assert MidiNote.A4 == 69

    def test_highest_note(self):
        """Test highest note G9 is 127."""
        assert MidiNote.G9 == 127

    def test_all_128_notes_exist(self):
        """Test all 128 MIDI notes have enum values."""
        # Get all enum values
        values = set(note.value for note in MidiNote)
        # Check all 0-127 are present
        for i in range(128):
            assert i in values, f"MIDI note {i} missing from enum"

    def test_enum_as_int(self):
        """Test MidiNote values work as integers."""
        assert int(MidiNote.C4) == 60
        assert MidiNote.C4 + 12 == 72  # Octave up

    def test_use_with_default_note(self):
        """Test MidiNote can be used with midi_track.default_note."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        midi_track.default_note = MidiNote.C4
        assert midi_track.default_note == 60

        midi_track.default_note = MidiNote.A4
        assert midi_track.default_note == 69

        midi_track.default_note = MidiNote.C_MINUS1
        assert midi_track.default_note == 0

        midi_track.default_note = MidiNote.G9
        assert midi_track.default_note == 127

    def test_sharps_are_correct(self):
        """Test sharp note values are correct."""
        # Check sharps in octave 4
        assert MidiNote.Cs4 == 61
        assert MidiNote.Ds4 == 63
        assert MidiNote.Fs4 == 66
        assert MidiNote.Gs4 == 68
        assert MidiNote.As4 == 70


class TestNoteLengthQuantization:
    """Note length quantization tests."""

    def test_quantize_exact_values(self):
        """Test that exact NoteLength values remain unchanged."""
        assert quantize_note_length(3) == 3
        assert quantize_note_length(6) == 6
        assert quantize_note_length(12) == 12
        assert quantize_note_length(24) == 24
        assert quantize_note_length(48) == 48

    def test_quantize_to_nearest(self):
        """Test that intermediate values snap to nearest."""
        # Between 3 and 6, midpoint is 4.5
        assert quantize_note_length(4) == 3  # closer to 3
        assert quantize_note_length(5) == 6  # closer to 6

        # Between 6 and 12, midpoint is 9
        assert quantize_note_length(8) == 6  # closer to 6
        assert quantize_note_length(10) == 12  # closer to 12

        # Between 12 and 24, midpoint is 18
        assert quantize_note_length(15) == 12  # closer to 12
        assert quantize_note_length(20) == 24  # closer to 24

        # Between 24 and 48, midpoint is 36
        assert quantize_note_length(30) == 24  # closer to 24
        assert quantize_note_length(40) == 48  # closer to 48

    def test_quantize_edge_cases(self):
        """Test boundary values."""
        assert quantize_note_length(0) == 3  # minimum clamps to THIRTY_SECOND
        assert quantize_note_length(1) == 3
        assert quantize_note_length(2) == 3
        assert quantize_note_length(100) == 48  # max clamps to HALF
        assert quantize_note_length(127) == 48


class TestNoteLengthPropertyQuantization:
    """Test that MIDI note length properties apply quantization."""

    def test_default_length_quantizes_on_write(self):
        """Test that writing a non-standard value gets quantized."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        midi_track.default_length = 10  # Should quantize to 12
        assert midi_track.default_length == 12

    def test_default_length_quantizes_on_read(self):
        """Test that reading quantizes to nearest valid value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        # Default is 6 (SIXTEENTH), should read back as 6
        assert midi_track.default_length == 6

    def test_arp_note_length_quantizes_on_write(self):
        """Test that arp_note_length writing quantizes."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        midi_track.arp_note_length = 30  # Should quantize to 24
        assert midi_track.arp_note_length == 24

    def test_note_length_enum_usage(self):
        """Test using NoteLength enum values directly."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        midi_track.default_length = NoteLength.QUARTER
        assert midi_track.default_length == 24

        midi_track.arp_note_length = NoteLength.EIGHTH
        assert midi_track.arp_note_length == 12


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

    @pytest.mark.slow
    def test_channel_roundtrip(self, temp_dir):
        """Test channel survives save/load."""
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).channel = 5
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        assert loaded.bank(1).part(1).midi_track(1).channel == 5

    @pytest.mark.slow
    def test_program_roundtrip(self, temp_dir):
        """Test program survives save/load."""
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).program = 64
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        assert loaded.bank(1).part(1).midi_track(1).program == 64

    @pytest.mark.slow
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

    @pytest.mark.slow
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

    @pytest.mark.slow
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

    @pytest.mark.slow
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


# =============================================================================
# Machine-Specific Part Track Tests
# =============================================================================

class TestFlexPartTrack:
    """FlexPartTrack machine-specific parameter tests."""

    def test_flex_track_factory(self):
        """Test getting a FlexPartTrack from Part."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        assert flex is not None

    def test_flex_pitch_default(self):
        """Test default pitch value."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        # Template default is 64 (no transpose)
        assert flex.pitch == 64

    def test_flex_set_pitch(self):
        """Test setting pitch."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        flex.pitch = 72
        assert flex.pitch == 72

    def test_flex_start_default(self):
        """Test default start value."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        assert flex.start == 0

    def test_flex_set_start(self):
        """Test setting start."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        flex.start = 32
        assert flex.start == 32

    def test_flex_length_default(self):
        """Test default length value."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        assert flex.length == 127  # Max length (full sample plays)

    def test_flex_rate_default(self):
        """Test default rate value."""
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        assert flex.rate == 127  # Template default (max)

    def test_flex_timestretch_mode_default(self):
        """Test default timestretch mode."""
        from octapy import TimestretchMode
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        assert flex.timestretch_mode == TimestretchMode.AUTO  # Template default

    def test_flex_set_timestretch_mode(self):
        """Test setting timestretch mode."""
        from octapy import TimestretchMode
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        flex.timestretch_mode = TimestretchMode.BEAT
        assert flex.timestretch_mode == TimestretchMode.BEAT

    def test_flex_all_tracks(self):
        """Test FlexPartTrack for all 8 tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            flex = part.flex_track(track_num)
            flex.pitch = 64 + track_num
            assert flex.pitch == 64 + track_num

    def test_flex_tracks_independent(self):
        """Test that different tracks have independent data."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        flex1 = part.flex_track(1)
        flex2 = part.flex_track(2)
        flex1.pitch = 50
        flex2.pitch = 70
        assert flex1.pitch == 50
        assert flex2.pitch == 70


class TestStaticPartTrack:
    """StaticPartTrack machine-specific parameter tests."""

    def test_static_track_factory(self):
        """Test getting a StaticPartTrack from Part."""
        project = Project.from_template("TEST")
        static = project.bank(1).part(1).static_track(1)
        assert static is not None

    def test_static_pitch_default(self):
        """Test default pitch value."""
        project = Project.from_template("TEST")
        static = project.bank(1).part(1).static_track(1)
        assert static.pitch == 64

    def test_static_set_pitch(self):
        """Test setting pitch."""
        project = Project.from_template("TEST")
        static = project.bank(1).part(1).static_track(1)
        static.pitch = 56
        assert static.pitch == 56


class TestThruPartTrack:
    """ThruPartTrack machine-specific parameter tests."""

    def test_thru_track_factory(self):
        """Test getting a ThruPartTrack from Part."""
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        assert thru is not None

    def test_thru_in_ab_default(self):
        """Test default in_ab value."""
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        assert thru.in_ab == 0

    def test_thru_set_in_ab(self):
        """Test setting in_ab."""
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        thru.in_ab = 1
        assert thru.in_ab == 1

    def test_thru_vol_ab_default(self):
        """Test default vol_ab value."""
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        assert thru.vol_ab == 64  # Template default

    def test_thru_set_vol_ab(self):
        """Test setting vol_ab."""
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        thru.vol_ab = 64
        assert thru.vol_ab == 64


class TestNeighborPartTrack:
    """NeighborPartTrack tests."""

    def test_neighbor_track_factory(self):
        """Test getting a NeighborPartTrack from Part."""
        project = Project.from_template("TEST")
        neighbor = project.bank(1).part(1).neighbor_track(1)
        assert neighbor is not None


class TestPickupPartTrack:
    """PickupPartTrack machine-specific parameter tests."""

    def test_pickup_track_factory(self):
        """Test getting a PickupPartTrack from Part."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        assert pickup is not None

    def test_pickup_pitch_default(self):
        """Test default pitch value."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        assert pickup.pitch == 64

    def test_pickup_set_pitch(self):
        """Test setting pitch."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        pickup.pitch = 72
        assert pickup.pitch == 72

    def test_pickup_direction_default(self):
        """Test default direction value."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        assert pickup.direction == 2  # Template default

    def test_pickup_gain_default(self):
        """Test default gain value."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        assert pickup.gain == 64  # Template default

    def test_pickup_set_gain(self):
        """Test setting gain."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        pickup.gain = 80
        assert pickup.gain == 80


class TestMachinePartTrackRoundTrip:
    """Test machine-specific part tracks survive save/load."""

    @pytest.mark.slow
    def test_flex_track_roundtrip(self, temp_dir):
        """Test FlexPartTrack values survive save/load."""
        from octapy import TimestretchMode
        project = Project.from_template("TEST")
        flex = project.bank(1).part(1).flex_track(1)
        flex.pitch = 72
        flex.start = 32
        flex.timestretch_mode = TimestretchMode.BEAT
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_flex = loaded.bank(1).part(1).flex_track(1)
        assert loaded_flex.pitch == 72
        assert loaded_flex.start == 32
        assert loaded_flex.timestretch_mode == TimestretchMode.BEAT

    @pytest.mark.slow
    def test_thru_track_roundtrip(self, temp_dir):
        """Test ThruPartTrack values survive save/load."""
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        thru.in_ab = 1
        thru.vol_ab = 80
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_thru = loaded.bank(1).part(1).thru_track(1)
        assert loaded_thru.in_ab == 1
        assert loaded_thru.vol_ab == 80

    @pytest.mark.slow
    def test_pickup_track_roundtrip(self, temp_dir):
        """Test PickupPartTrack values survive save/load."""
        project = Project.from_template("TEST")
        pickup = project.bank(1).part(1).pickup_track(1)
        pickup.pitch = 60
        pickup.gain = 90
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_pickup = loaded.bank(1).part(1).pickup_track(1)
        assert loaded_pickup.pitch == 60
        assert loaded_pickup.gain == 90


# =============================================================================
# ThruInput Enum Tests
# =============================================================================

class TestThruInputEnum:
    """ThruInput enum tests for Thru machine input selection."""

    def test_thru_in_ab_returns_enum(self):
        """Test that in_ab returns ThruInput enum."""
        from octapy import ThruInput
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        assert isinstance(thru.in_ab, ThruInput)

    def test_thru_set_in_ab_with_enum(self):
        """Test setting in_ab with ThruInput enum."""
        from octapy import ThruInput
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        thru.in_ab = ThruInput.A_PLUS_B
        assert thru.in_ab == ThruInput.A_PLUS_B

    def test_thru_set_in_ab_with_int(self):
        """Test setting in_ab with integer."""
        from octapy import ThruInput
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        thru.in_ab = 2  # ThruInput.A
        assert thru.in_ab == ThruInput.A

    def test_thru_in_cd_returns_enum(self):
        """Test that in_cd returns ThruInput enum."""
        from octapy import ThruInput
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)
        assert isinstance(thru.in_cd, ThruInput)

    def test_thru_all_input_values(self):
        """Test all ThruInput enum values."""
        from octapy import ThruInput
        project = Project.from_template("TEST")
        thru = project.bank(1).part(1).thru_track(1)

        for input_val in [ThruInput.OFF, ThruInput.A_PLUS_B, ThruInput.A, ThruInput.B, ThruInput.A_B]:
            thru.in_ab = input_val
            assert thru.in_ab == input_val


# =============================================================================
# MIDI Part Track Note2/3/4 Tests
# =============================================================================

class TestMidiPartTrackChordNotes:
    """MidiPartTrack chord note (note2/3/4) tests."""

    def test_default_note2_default(self):
        """Test default note2 value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_note2 == 64  # Template default (no offset)

    def test_set_default_note2(self):
        """Test setting default_note2."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note2 = 71  # +7 semitones
        assert midi_track.default_note2 == 71

    def test_default_note3_default(self):
        """Test default note3 value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_note3 == 64  # Template default (no offset)

    def test_set_default_note3(self):
        """Test setting default_note3."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note3 = 76  # +12 semitones (octave)
        assert midi_track.default_note3 == 76

    def test_default_note4_default(self):
        """Test default note4 value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_note4 == 64  # Template default (no offset)

    def test_set_default_note4(self):
        """Test setting default_note4."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note4 = 52  # -12 semitones (octave down)
        assert midi_track.default_note4 == 52

    def test_chord_notes_independent(self):
        """Test that chord notes are independent."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note2 = 67
        midi_track.default_note3 = 71
        midi_track.default_note4 = 76
        assert midi_track.default_note2 == 67
        assert midi_track.default_note3 == 71
        assert midi_track.default_note4 == 76

    @pytest.mark.slow
    def test_chord_notes_roundtrip(self, temp_dir):
        """Test chord notes survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.default_note2 = 67  # Perfect 5th
        midi_track.default_note3 = 71  # Major 7th
        midi_track.default_note4 = 76  # Octave
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_midi = loaded.bank(1).part(1).midi_track(1)
        assert loaded_midi.default_note2 == 67
        assert loaded_midi.default_note3 == 71
        assert loaded_midi.default_note4 == 76


# =============================================================================
# AMP Page Tests (AudioPartTrack)
# =============================================================================

class TestAudioPartTrackAmpPage:
    """AudioPartTrack AMP page parameter tests."""

    def test_attack_default(self):
        """Test default attack value."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        assert track.attack == 0

    def test_set_attack(self):
        """Test setting attack."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.attack = 64
        assert track.attack == 64

    def test_hold_default(self):
        """Test default hold value."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        assert track.hold == 127

    def test_set_hold(self):
        """Test setting hold."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.hold = 64
        assert track.hold == 64

    def test_release_default(self):
        """Test default release value."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        assert track.release == 127

    def test_set_release(self):
        """Test setting release."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.release = 100
        assert track.release == 100

    def test_amp_volume_default(self):
        """Test default amp volume value."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        assert track.amp_volume == 64

    def test_set_amp_volume(self):
        """Test setting amp volume."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.amp_volume = 80
        assert track.amp_volume == 80

    def test_balance_default(self):
        """Test default balance value."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        assert track.balance == 64

    def test_set_balance(self):
        """Test setting balance."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.balance = 32  # Pan left
        assert track.balance == 32

    def test_amp_all_tracks(self):
        """Test AMP page for all 8 tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            track = part.track(track_num)
            track.attack = track_num * 10
            assert track.attack == track_num * 10

    @pytest.mark.slow
    def test_amp_roundtrip(self, temp_dir):
        """Test AMP parameters survive save/load."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        track.attack = 30
        track.hold = 80
        track.release = 50
        track.amp_volume = 90
        track.balance = 40
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_track = loaded.bank(1).part(1).track(1)
        assert loaded_track.attack == 30
        assert loaded_track.hold == 80
        assert loaded_track.release == 50
        assert loaded_track.amp_volume == 90
        assert loaded_track.balance == 40


# =============================================================================
# ARP Page Tests (MidiPartTrack)
# =============================================================================

class TestMidiPartTrackArpPage:
    """MidiPartTrack ARP page parameter tests."""

    def test_arp_transpose_default(self):
        """Test default arp_transpose value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.arp_transpose == 64  # No transpose

    def test_set_arp_transpose(self):
        """Test setting arp_transpose."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_transpose = 76  # +12 semitones
        assert midi_track.arp_transpose == 76

    def test_arp_legato_default(self):
        """Test default arp_legato value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.arp_legato == 0

    def test_set_arp_legato(self):
        """Test setting arp_legato."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_legato = 64
        assert midi_track.arp_legato == 64

    def test_arp_mode_default(self):
        """Test default arp_mode value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.arp_mode == 0

    def test_set_arp_mode(self):
        """Test setting arp_mode."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_mode = 3
        assert midi_track.arp_mode == 3

    def test_arp_speed_default(self):
        """Test default arp_speed value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.arp_speed == 5

    def test_set_arp_speed(self):
        """Test setting arp_speed."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_speed = 48
        assert midi_track.arp_speed == 48

    def test_arp_range_default(self):
        """Test default arp_range value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.arp_range == 0

    def test_set_arp_range(self):
        """Test setting arp_range."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_range = 24
        assert midi_track.arp_range == 24

    def test_arp_note_length_default(self):
        """Test default arp_note_length value."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.arp_note_length == 6

    def test_set_arp_note_length(self):
        """Test setting arp_note_length."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_note_length = 12
        assert midi_track.arp_note_length == 12

    def test_arp_all_tracks(self):
        """Test ARP page for all 8 MIDI tracks."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        for track_num in range(1, 9):
            midi_track = part.midi_track(track_num)
            midi_track.arp_transpose = 64 + track_num
            assert midi_track.arp_transpose == 64 + track_num

    @pytest.mark.slow
    def test_arp_roundtrip(self, temp_dir):
        """Test ARP parameters survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        midi_track.arp_transpose = 76
        midi_track.arp_legato = 64
        midi_track.arp_mode = 2
        midi_track.arp_speed = 48
        midi_track.arp_range = 24
        midi_track.arp_note_length = 12
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_midi = loaded.bank(1).part(1).midi_track(1)
        assert loaded_midi.arp_transpose == 76
        assert loaded_midi.arp_legato == 64
        assert loaded_midi.arp_mode == 2
        assert loaded_midi.arp_speed == 48
        assert loaded_midi.arp_range == 24
        assert loaded_midi.arp_note_length == 12
