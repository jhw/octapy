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
