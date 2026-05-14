"""
Tests for enums and quantization functions.

These tests verify that enum values match Octatrack specifications
and that quantization functions work correctly.
"""

import pytest

from octapy import Project, NoteLength
from octapy.api.enums import MidiNote
from octapy.api.utils import quantize_note_length


# =============================================================================
# NoteLength Enum Tests
# =============================================================================

class TestNoteLengthEnum:
    """NoteLength enum tests."""

    def test_enum_values(self):
        """Test NoteLength enum has correct MIDI tick values."""
        assert NoteLength.THIRTY_SECOND == 3
        assert NoteLength.SIXTEENTH == 6
        assert NoteLength.EIGHTH == 12
        assert NoteLength.THREE_SIXTEENTHS == 18
        assert NoteLength.QUARTER == 24
        assert NoteLength.FIVE_SIXTEENTHS == 30
        assert NoteLength.THREE_EIGHTHS == 36
        assert NoteLength.SEVEN_SIXTEENTHS == 42
        assert NoteLength.HALF == 48
        assert NoteLength.NINE_SIXTEENTHS == 54
        assert NoteLength.FIVE_EIGHTHS == 60
        assert NoteLength.ELEVEN_SIXTEENTHS == 66
        assert NoteLength.THREE_QUARTERS == 72
        assert NoteLength.THIRTEEN_SIXTEENTHS == 78
        assert NoteLength.SEVEN_EIGHTHS == 84
        assert NoteLength.FIFTEEN_SIXTEENTHS == 90
        assert NoteLength.WHOLE == 96
        assert NoteLength.SEVENTEEN_SIXTEENTHS == 102
        assert NoteLength.NINE_EIGHTHS == 108
        assert NoteLength.NINETEEN_SIXTEENTHS == 114
        assert NoteLength.FIVE_QUARTERS == 120
        assert NoteLength.TWENTYONE_SIXTEENTHS == 126
        assert NoteLength.INFINITY == 127

    def test_enum_as_int(self):
        """Test NoteLength values work as integers."""
        assert int(NoteLength.SIXTEENTH) == 6
        assert NoteLength.QUARTER * 2 == 48


# =============================================================================
# MidiNote Enum Tests
# =============================================================================

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
        values = set(note.value for note in MidiNote)
        for i in range(128):
            assert i in values, f"MIDI note {i} missing from enum"

    def test_enum_as_int(self):
        """Test MidiNote values work as integers."""
        assert int(MidiNote.C4) == 60
        assert MidiNote.C4 + 12 == 72  # Octave up

    def test_sharps_are_correct(self):
        """Test sharp note values are correct."""
        assert MidiNote.Cs4 == 61
        assert MidiNote.Ds4 == 63
        assert MidiNote.Fs4 == 66
        assert MidiNote.Gs4 == 68
        assert MidiNote.As4 == 70


# =============================================================================
# ThruInput Enum Tests
# =============================================================================

class TestThruInputEnum:
    """ThruInput enum tests."""

    def test_thru_input_enum_values(self):
        """Test ThruInput enum values exist."""
        from octapy import ThruInput
        assert ThruInput.OFF.value == 0
        assert ThruInput.A_PLUS_B.value == 1
        assert ThruInput.A.value == 2
        assert ThruInput.B.value == 3
        assert ThruInput.A_B.value == 4


# =============================================================================
# RetrigTime Enum Tests
# =============================================================================

class TestRetrigTimeEnum:
    """RetrigTime enum tests."""

    def test_retrig_time_enum_values(self):
        """Test RetrigTime enum values."""
        from octapy.api.enums import RetrigTime
        assert RetrigTime.HALF == 79  # Machine default

    def test_enum_as_int(self):
        """Test RetrigTime values work as integers."""
        from octapy.api.enums import RetrigTime
        assert int(RetrigTime.HALF) == 79


# =============================================================================
# Note Length Quantization Tests
# =============================================================================

class TestNoteLengthQuantization:
    """Note length quantization tests."""

    def test_quantize_exact_values(self):
        """Test that exact NoteLength values remain unchanged."""
        valid_values = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 127]
        for value in valid_values:
            assert quantize_note_length(value) == value

    def test_quantize_to_nearest(self):
        """Test that intermediate values snap to nearest valid value."""
        # Between 3 and 6, midpoint is 4.5
        assert quantize_note_length(4) == 3   # closer to 3
        assert quantize_note_length(5) == 6   # closer to 6

        # Between 6 and 12, midpoint is 9
        assert quantize_note_length(8) == 6   # closer to 6
        assert quantize_note_length(10) == 12  # closer to 12

        # Between 12 and 18, midpoint is 15
        assert quantize_note_length(14) == 12  # closer to 12
        assert quantize_note_length(16) == 18  # closer to 18

        # Between 126 and 127
        assert quantize_note_length(126) == 126
        assert quantize_note_length(127) == 127

    def test_quantize_edge_cases(self):
        """Test boundary values."""
        assert quantize_note_length(0) == 3    # minimum clamps to THIRTY_SECOND
        assert quantize_note_length(1) == 3
        assert quantize_note_length(2) == 3
        assert quantize_note_length(127) == 127  # INFINITY
        assert quantize_note_length(200) == 127  # max clamps to INFINITY


class TestNoteLengthPropertyQuantization:
    """Test that MIDI note length properties apply quantization."""

    def test_default_length_quantizes_on_write(self):
        """Test that writing a non-standard value gets quantized."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        midi_track.default_length = 10  # Should quantize to 12
        assert midi_track.default_length == 12

    def test_arp_note_length_quantizes_on_write(self):
        """Test that arp_note_length writing quantizes to nearest multiple of 6."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        # 30 is a valid value (FIVE_SIXTEENTHS)
        midi_track.arp_note_length = 30
        assert midi_track.arp_note_length == 30

        # 31 should quantize to 30 (nearest multiple of 6)
        midi_track.arp_note_length = 31
        assert midi_track.arp_note_length == 30

        # 33 should quantize to 36 (nearest multiple of 6)
        midi_track.arp_note_length = 34
        assert midi_track.arp_note_length == 36

    def test_note_length_enum_usage(self):
        """Test using NoteLength enum values directly."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        midi_track.default_length = NoteLength.QUARTER
        assert midi_track.default_length == 24

        midi_track.arp_note_length = NoteLength.EIGHTH
        assert midi_track.arp_note_length == 12


# =============================================================================
# AudioPartTrack.to_dict / from_dict round-trip
# =============================================================================

from octapy import AudioPartTrack, MachineType


class TestAudioPartTrackDictRoundTrip:
    """to_dict / from_dict must preserve every field that the OT
    binary format encodes for a part-track. Regression: prior to
    v0.2.2, from_dict ignored fx*_params, src/setup pages, and LFO
    setup, so dict round-trip silently dropped those bytes.
    """

    def _set_distinct_fields(self, t: AudioPartTrack):
        """Mutate every dimension we want to verify round-trips."""
        t.fx1_type = 17  # FLANGER
        t.fx2_type = 22  # DARK_REVERB
        for i, v in enumerate([10, 20, 30, 40, 50, 60], start=1):
            setattr(t, f"fx1_param{i}", v)
        for i, v in enumerate([7, 14, 21, 28, 35, 42], start=1):
            setattr(t, f"fx2_param{i}", v)
        t.attack = 5
        t.hold = 100
        t.release = 50
        t.amp_volume = 96
        t.balance = 80
        for i, v in enumerate([1, 2, 3, 4, 5, 6], start=1):
            t.src._set_param(i, v)
        for i, v in enumerate([6, 5, 4, 3, 2, 1], start=1):
            t.setup._set_param(i, v)
        for n, (dest, wave, mult, trig, spd, dep) in enumerate(
            [(18, 1, 2, 1, 32, 64), (19, 2, 0, 3, 16, 90), (20, 3, 1, 0, 48, 32)],
            start=1,
        ):
            lfo = t.lfo(n)
            lfo.destination = dest
            lfo.waveform = wave
            lfo.multiplier = mult
            lfo.trig_mode = trig
            lfo.speed = spd
            lfo.depth = dep

    def test_dict_round_trip_is_idempotent(self):
        """to_dict → from_dict → to_dict produces the same dict.

        Captures the contract: dict round-trip preserves the active
        machine's configured state (FX, AMP, SRC/setup of the active
        machine, LFOs, recorder, volume, slot pointers). The underlying
        byte buffer also holds SRC/setup pages for the four *inactive*
        machine types — those aren't exposed by the public API and
        aren't expected to survive a dict round-trip.
        """
        project = Project.from_template("DICT RT")
        original = project.bank(1).part(1).audio_track(2)
        original.machine_type = MachineType.NEIGHBOR
        self._set_distinct_fields(original)

        d1 = original.to_dict()
        restored = AudioPartTrack.from_dict(d1)
        d2 = restored.to_dict()
        assert d1 == d2, "to_dict → from_dict → to_dict not idempotent"

    def test_dict_round_trip_preserves_fx_params(self):
        """Specifically check that FX param tables aren't dropped."""
        project = Project.from_template("FX RT")
        t = project.bank(1).part(1).audio_track(1)
        t.fx1_type = 4  # FILTER
        for i, v in enumerate([42, 76, 32, 0, 100, 64], start=1):
            setattr(t, f"fx1_param{i}", v)

        restored = AudioPartTrack.from_dict(t.to_dict())
        for i in range(1, 7):
            assert getattr(restored, f"fx1_param{i}") == getattr(t, f"fx1_param{i}"), (
                f"fx1_param{i} dropped on round-trip"
            )

    def test_dict_round_trip_preserves_lfos(self):
        """LFO destination + waveform + spd/dep survive dict round-trip."""
        project = Project.from_template("LFO RT")
        t = project.bank(1).part(1).audio_track(1)
        lfo1 = t.lfo(1)
        lfo1.destination = 18  # fx1.base
        lfo1.waveform = 1
        lfo1.speed = 64
        lfo1.depth = 100

        restored = AudioPartTrack.from_dict(t.to_dict())
        assert restored.lfo(1).destination == 18
        assert restored.lfo(1).waveform == 1
        assert restored.lfo(1).speed == 64
        assert restored.lfo(1).depth == 100

    def test_dict_omitting_new_fields_still_loads(self):
        """Backwards compat: a pre-v0.2.2 dict (no fx_params / lfos /
        src_params / setup_params) still loads."""
        old_style_dict = {
            "track": 3,
            "machine_type": "NEIGHBOR",
            "static_slot": 0,
            "flex_slot": 0,
            "volume": {"main": 108, "cue": 0},
            "amp": {"attack": 0, "hold": 127, "release": 24, "volume": 108, "balance": 64},
            "fx1_type": 4,
            "fx2_type": 8,
            "recorder": {"source": "OFF", "rlen": 16, "trig": "ONE2", "loop": False,
                         "fin": 0, "fout": 0, "ab_gain": 0, "qrec": "OFF", "qpl": 255,
                         "cd_gain": 0},
        }
        track = AudioPartTrack.from_dict(old_style_dict)
        assert track.machine_type == MachineType.NEIGHBOR
        assert track.fx1_type == 4
