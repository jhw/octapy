"""
Tests for Pattern, AudioPatternTrack, and AudioStep high-level API.
"""

import pytest

from octapy import Project, MachineType, TrigCondition
from octapy._io import BankFile


class TestPatternBasics:
    """Basic Pattern tests via high-level API."""

    def test_pattern_from_bank(self):
        """Test getting a pattern from a bank."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)
        assert pattern is not None

    def test_pattern_part_assignment(self):
        """Test pattern part assignment."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        pattern.part = 2
        assert pattern.part == 2

        pattern.part = 4
        assert pattern.part == 4


class TestAudioPatternTrack:
    """AudioPatternTrack (sequence data) tests."""

    def test_get_pattern_track(self):
        """Test getting an AudioPatternTrack."""
        project = Project.from_template("TEST")
        pattern_track = project.bank(1).pattern(1).track(1)
        steps = pattern_track.active_steps
        assert isinstance(steps, list)

    def test_set_active_steps(self):
        """Test setting active trigger steps."""
        project = Project.from_template("TEST")
        pattern_track = project.bank(1).pattern(1).track(1)

        steps = [1, 5, 9, 13]
        pattern_track.active_steps = steps

        assert pattern_track.active_steps == steps

    def test_set_active_steps_all_16(self):
        """Test setting all 16 trigger steps."""
        project = Project.from_template("TEST")
        pattern_track = project.bank(1).pattern(1).track(1)

        steps = list(range(1, 17))
        pattern_track.active_steps = steps

        assert pattern_track.active_steps == steps

    def test_set_active_steps_extended(self):
        """Test setting extended trigger steps (17-64)."""
        project = Project.from_template("TEST")
        pattern_track = project.bank(1).pattern(1).track(1)

        steps = [17, 33, 49, 64]
        pattern_track.active_steps = steps

        assert pattern_track.active_steps == steps

    def test_clear_active_steps(self):
        """Test clearing trigger steps."""
        project = Project.from_template("TEST")
        pattern_track = project.bank(1).pattern(1).track(1)

        # Set some steps
        pattern_track.active_steps = [1, 5, 9, 13]

        # Clear them
        pattern_track.active_steps = []

        assert pattern_track.active_steps == []


class TestAudioStep:
    """AudioStep (individual step) tests."""

    def test_get_step(self):
        """Test getting an AudioStep."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step is not None

    def test_step_active_property(self):
        """Test step active property."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        # Initially not active
        step.active = False
        assert step.active is False

        # Set active
        step.active = True
        assert step.active is True

        # Verify appears in active_steps
        assert 5 in project.bank(1).pattern(1).track(1).active_steps

    def test_step_trigless_property(self):
        """Test step trigless property."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.trigless = True
        assert step.trigless is True

        # Verify appears in trigless_steps
        assert 5 in project.bank(1).pattern(1).track(1).trigless_steps

    def test_step_matches_active_steps(self):
        """Test that AudioStep.active matches active_steps list."""
        project = Project.from_template("TEST")
        pattern_track = project.bank(1).pattern(1).track(1)

        # Set via active_steps
        pattern_track.active_steps = [1, 5, 9, 13]

        # Verify via Step
        assert pattern_track.step(1).active is True
        assert pattern_track.step(5).active is True
        assert pattern_track.step(9).active is True
        assert pattern_track.step(13).active is True
        assert pattern_track.step(2).active is False
        assert pattern_track.step(6).active is False

    def test_step_condition_default(self):
        """Test step condition defaults to NONE."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.condition == TrigCondition.NONE


class TestMultipleTracks:
    """Tests for multiple tracks in a pattern."""

    def test_independent_track_data(self):
        """Test that tracks have independent trigger data."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        # Set different steps on each track
        track_steps = {
            1: [1, 5, 9, 13],
            2: [5, 13],
            3: [1, 2, 3, 4],
            4: [9, 10, 11, 12],
        }

        for track_num, steps in track_steps.items():
            pattern.track(track_num).active_steps = steps

        # Verify each track has its own steps
        for track_num, expected in track_steps.items():
            result = pattern.track(track_num).active_steps
            assert result == expected, f"Track {track_num} mismatch"


class TestPatternRoundTrip:
    """Pattern read/write round-trip tests."""

    @pytest.mark.slow
    def test_pattern_survives_save(self, temp_dir):
        """Test that pattern data survives save/load."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        # Set some pattern data
        pattern.track(1).active_steps = [1, 5, 9, 13]
        pattern.track(2).active_steps = [5, 13]

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        # Verify
        assert loaded.bank(1).pattern(1).track(1).active_steps == [1, 5, 9, 13]
        assert loaded.bank(1).pattern(1).track(2).active_steps == [5, 13]


class TestStepCondition:
    """Step trig condition tests."""

    def test_set_condition_fill(self):
        """Test setting FILL condition."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.condition = TrigCondition.FILL
        assert step.condition == TrigCondition.FILL

    def test_set_condition_probability(self):
        """Test setting probability condition."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.condition = TrigCondition.PERCENT_50
        assert step.condition == TrigCondition.PERCENT_50

    def test_set_condition_loop(self):
        """Test setting loop condition (1:2)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.condition = TrigCondition.T1_R2
        assert step.condition == TrigCondition.T1_R2

    def test_clear_condition(self):
        """Test clearing condition back to NONE."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.condition = TrigCondition.FILL
        step.condition = TrigCondition.NONE
        assert step.condition == TrigCondition.NONE

    def test_condition_independent_per_step(self):
        """Test that conditions are independent per step."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)

        track.step(1).condition = TrigCondition.FILL
        track.step(5).condition = TrigCondition.PERCENT_50
        track.step(9).condition = TrigCondition.T1_R4

        assert track.step(1).condition == TrigCondition.FILL
        assert track.step(5).condition == TrigCondition.PERCENT_50
        assert track.step(9).condition == TrigCondition.T1_R4
        assert track.step(2).condition == TrigCondition.NONE


class TestStepPlocks:
    """Step p-lock (parameter lock) tests."""

    def test_volume_default_none(self):
        """Test volume p-lock defaults to None (disabled)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.volume is None

    def test_set_volume(self):
        """Test setting volume p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.volume = 100
        assert step.volume == 100

    def test_clear_volume(self):
        """Test clearing volume p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.volume = 100
        step.volume = None
        assert step.volume is None

    def test_pitch_default_none(self):
        """Test pitch p-lock defaults to None (disabled)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.pitch is None

    def test_set_pitch(self):
        """Test setting pitch p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.pitch = 76  # One octave up from center (64)
        assert step.pitch == 76

    def test_set_pitch_low(self):
        """Test setting low pitch."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.pitch = 52  # One octave down from center
        assert step.pitch == 52

    def test_sample_lock_default_none(self):
        """Test sample lock defaults to None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.sample_lock is None

    def test_set_sample_lock(self):
        """Test setting sample lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.sample_lock = 3  # Lock to slot 3 (0-indexed)
        assert step.sample_lock == 3

    def test_plocks_independent_per_step(self):
        """Test that p-locks are independent per step."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)

        track.step(1).volume = 50
        track.step(5).volume = 100
        track.step(9).volume = 75

        assert track.step(1).volume == 50
        assert track.step(5).volume == 100
        assert track.step(9).volume == 75
        assert track.step(2).volume is None

    def test_plocks_independent_per_track(self):
        """Test that p-locks are independent per track."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        pattern.track(1).step(1).volume = 50
        pattern.track(2).step(1).volume = 100

        assert pattern.track(1).step(1).volume == 50
        assert pattern.track(2).step(1).volume == 100


class TestStepProbability:
    """Step probability property tests."""

    def test_probability_default_none(self):
        """Test probability defaults to None (no probability condition)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.probability is None

    def test_set_probability_50(self):
        """Test setting 50% probability."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.probability = 0.5
        assert step.probability == 0.5
        assert step.condition == TrigCondition.PERCENT_50

    def test_set_probability_25(self):
        """Test setting 25% probability."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.probability = 0.25
        assert step.probability == 0.25

    def test_set_probability_closest_match(self):
        """Test that setting probability finds closest match."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        # 0.30 should map to 0.33 (closest)
        step.probability = 0.30
        assert step.probability == 0.33

        # 0.70 should map to 0.67 (closest)
        step.probability = 0.70
        assert step.probability == 0.67

    def test_clear_probability_with_none(self):
        """Test clearing probability with None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.probability = 0.5
        step.probability = None
        assert step.probability is None
        assert step.condition == TrigCondition.NONE

    def test_clear_probability_with_1(self):
        """Test clearing probability with 1.0 (always trigger)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.probability = 0.5
        step.probability = 1.0
        assert step.probability is None

    def test_probability_not_returned_for_other_conditions(self):
        """Test that probability returns None for non-probability conditions."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(5)

        step.condition = TrigCondition.FILL
        assert step.probability is None

        step.condition = TrigCondition.T1_R4
        assert step.probability is None


class TestPlockRoundTrip:
    """P-lock read/write round-trip tests."""

    @pytest.mark.slow
    def test_plocks_survive_save(self, temp_dir):
        """Test that p-lock data survives save/load."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)

        # Set various p-locks
        track.step(1).volume = 50
        track.step(5).pitch = 76
        track.step(9).condition = TrigCondition.FILL

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        # Verify
        loaded_track = loaded.bank(1).pattern(1).track(1)
        assert loaded_track.step(1).volume == 50
        assert loaded_track.step(5).pitch == 76
        assert loaded_track.step(9).condition == TrigCondition.FILL

    @pytest.mark.slow
    def test_probability_survives_save(self, temp_dir):
        """Test that probability survives save/load."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)

        track.step(5).probability = 0.5

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.bank(1).pattern(1).track(1).step(5).probability == 0.5

    @pytest.mark.slow
    def test_tempo_survives_save(self, temp_dir):
        """Test that tempo survives save/load."""
        project = Project.from_template("TEST")
        project.settings.tempo = 124.0

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.settings.tempo == 124.0


# =============================================================================
# MIDI Pattern Track Tests
# =============================================================================

class TestMidiPatternTrackBasics:
    """MidiPatternTrack basic tests."""

    def test_get_midi_pattern_track(self):
        """Test getting a MidiPatternTrack."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        assert midi_track is not None

    def test_get_all_midi_tracks(self):
        """Test getting all 8 MIDI tracks."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)
        for i in range(1, 9):
            midi_track = pattern.midi_track(i)
            assert midi_track is not None

    def test_midi_active_steps_default_empty(self):
        """Test MIDI active steps default to empty."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        assert midi_track.active_steps == []


class TestMidiPatternTrackSteps:
    """MidiPatternTrack step operations tests."""

    def test_set_active_steps(self):
        """Test setting active trigger steps."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        steps = [1, 5, 9, 13]
        midi_track.active_steps = steps

        assert midi_track.active_steps == steps

    def test_set_active_steps_extended(self):
        """Test setting extended trigger steps (17-64)."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        steps = [17, 33, 49, 64]
        midi_track.active_steps = steps

        assert midi_track.active_steps == steps

    def test_clear_active_steps(self):
        """Test clearing trigger steps."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.active_steps = [1, 5, 9, 13]
        midi_track.active_steps = []

        assert midi_track.active_steps == []

    def test_trigless_steps(self):
        """Test setting trigless steps."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.trigless_steps = [2, 6, 10, 14]
        assert midi_track.trigless_steps == [2, 6, 10, 14]


class TestMidiStep:
    """MidiStep (individual step) tests."""

    def test_get_step(self):
        """Test getting a MidiStep."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step is not None

    def test_step_active_property(self):
        """Test step active property."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.active = True
        assert step.active is True

        # Verify appears in active_steps
        assert 5 in project.bank(1).pattern(1).midi_track(1).active_steps

    def test_step_trigless_property(self):
        """Test step trigless property."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.trigless = True
        assert step.trigless is True

    def test_step_matches_active_steps(self):
        """Test that MidiStep.active matches active_steps list."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.active_steps = [1, 5, 9, 13]

        assert midi_track.step(1).active is True
        assert midi_track.step(5).active is True
        assert midi_track.step(9).active is True
        assert midi_track.step(13).active is True
        assert midi_track.step(2).active is False


class TestMidiStepPlocks:
    """MidiStep p-lock (parameter lock) tests."""

    def test_note_default_none(self):
        """Test note p-lock defaults to None (disabled)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.note is None

    def test_set_note(self):
        """Test setting note p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.note = 60  # Middle C
        assert step.note == 60

    def test_clear_note(self):
        """Test clearing note p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.note = 60
        step.note = None
        assert step.note is None

    def test_velocity_default_none(self):
        """Test velocity p-lock defaults to None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.velocity is None

    def test_set_velocity(self):
        """Test setting velocity p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.velocity = 100
        assert step.velocity == 100

    def test_length_default_none(self):
        """Test length p-lock defaults to None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.length is None

    def test_set_length(self):
        """Test setting length p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.length = 12  # 1/8 note
        assert step.length == 12

    def test_plocks_independent_per_step(self):
        """Test that p-locks are independent per step."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.step(1).note = 48  # C3
        midi_track.step(5).note = 60  # C4
        midi_track.step(9).note = 72  # C5

        assert midi_track.step(1).note == 48
        assert midi_track.step(5).note == 60
        assert midi_track.step(9).note == 72
        assert midi_track.step(2).note is None

    def test_plocks_independent_per_track(self):
        """Test that p-locks are independent per track."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        pattern.midi_track(1).step(1).note = 48
        pattern.midi_track(2).step(1).note = 60

        assert pattern.midi_track(1).step(1).note == 48
        assert pattern.midi_track(2).step(1).note == 60


class TestMidiStepCCPlocks:
    """MidiStep CC p-lock tests."""

    def test_pitch_bend_default_none(self):
        """Test pitch_bend p-lock defaults to None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.pitch_bend is None

    def test_set_pitch_bend(self):
        """Test setting pitch_bend p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.pitch_bend = 100
        assert step.pitch_bend == 100

    def test_clear_pitch_bend(self):
        """Test clearing pitch_bend p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.pitch_bend = 100
        step.pitch_bend = None
        assert step.pitch_bend is None

    def test_aftertouch_default_none(self):
        """Test aftertouch p-lock defaults to None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.aftertouch is None

    def test_set_aftertouch(self):
        """Test setting aftertouch p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.aftertouch = 80
        assert step.aftertouch == 80

    def test_cc_default_none(self):
        """Test cc p-lock defaults to None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.cc(1) is None

    def test_set_cc(self):
        """Test setting cc p-lock."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.set_cc(1, 64)
        assert step.cc(1) == 64

    def test_set_all_cc_plocks(self):
        """Test setting all CC p-locks (1-10)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        for i in range(1, 11):
            step.set_cc(i, i * 10)

        for i in range(1, 11):
            assert step.cc(i) == i * 10, f"CC{i} mismatch"

    def test_cc_plocks_independent_per_step(self):
        """Test that CC p-locks are independent per step."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.step(1).set_cc(1, 20)
        midi_track.step(5).set_cc(1, 64)
        midi_track.step(9).set_cc(1, 100)

        assert midi_track.step(1).cc(1) == 20
        assert midi_track.step(5).cc(1) == 64
        assert midi_track.step(9).cc(1) == 100
        assert midi_track.step(2).cc(1) is None

    def test_cc_invalid_slot(self):
        """Test invalid CC slot raises ValueError."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        with pytest.raises(ValueError):
            step.cc(0)
        with pytest.raises(ValueError):
            step.cc(11)


class TestMidiStepLengthQuantization:
    """MidiStep length p-lock quantization tests."""

    def test_length_exact_values(self):
        """Test exact NoteLength values are preserved."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        # Test all valid NoteLength values: 3, multiples of 6 from 6-126, and 127
        valid_values = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 127]
        for expected in valid_values:
            step.length = expected
            assert step.length == expected, f"Expected {expected}, got {step.length}"

    def test_length_quantizes_to_nearest(self):
        """Test non-NoteLength values are quantized to nearest valid value."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        # Values close to 3 (1/32)
        step.length = 1
        assert step.length == 3
        step.length = 4
        assert step.length == 3

        # Values close to 6 (1/16)
        step.length = 5
        assert step.length == 6
        step.length = 8
        assert step.length == 6

        # Values close to 12 (1/8)
        step.length = 10
        assert step.length == 12
        step.length = 14
        assert step.length == 12

        # Values close to 18 (3/16)
        step.length = 16
        assert step.length == 18
        step.length = 20
        assert step.length == 18

        # Values close to 24 (1/4)
        step.length = 22
        assert step.length == 24
        step.length = 26
        assert step.length == 24

        # Values close to 48 (1/2)
        step.length = 46
        assert step.length == 48
        step.length = 50
        assert step.length == 48

        # Values close to 96 (whole note)
        step.length = 94
        assert step.length == 96
        step.length = 98
        assert step.length == 96

    def test_length_clear_with_none(self):
        """Test clearing length p-lock with None."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.length = 12
        assert step.length == 12
        step.length = None
        assert step.length is None

    def test_length_zero_quantizes_to_minimum(self):
        """Test zero value quantizes to minimum (3)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.length = 0
        assert step.length == 3

    def test_length_large_value_quantizes_to_maximum(self):
        """Test large values quantize to maximum (127)."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.length = 127
        assert step.length == 127

        step.length = 200
        assert step.length == 127


class TestMidiStepCondition:
    """MidiStep condition tests."""

    def test_condition_default_none(self):
        """Test condition defaults to NONE."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.condition == TrigCondition.NONE

    def test_set_condition_fill(self):
        """Test setting FILL condition."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.condition = TrigCondition.FILL
        assert step.condition == TrigCondition.FILL

    def test_set_probability(self):
        """Test setting probability."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(5)

        step.probability = 0.5
        assert step.probability == 0.5


class TestMidiPatternRoundTrip:
    """MIDI pattern read/write round-trip tests."""

    @pytest.mark.slow
    def test_active_steps_survive_save(self, temp_dir):
        """Test that MIDI active steps survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.active_steps = [1, 5, 9, 13]

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.bank(1).pattern(1).midi_track(1).active_steps == [1, 5, 9, 13]

    @pytest.mark.slow
    def test_plocks_survive_save(self, temp_dir):
        """Test that MIDI p-locks survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.step(1).note = 48
        midi_track.step(5).velocity = 100
        midi_track.step(9).length = 12

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        loaded_track = loaded.bank(1).pattern(1).midi_track(1)
        assert loaded_track.step(1).note == 48
        assert loaded_track.step(5).velocity == 100
        assert loaded_track.step(9).length == 12

    @pytest.mark.slow
    def test_condition_survives_save(self, temp_dir):
        """Test that MIDI conditions survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.step(5).condition = TrigCondition.FILL

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.bank(1).pattern(1).midi_track(1).step(5).condition == TrigCondition.FILL

    @pytest.mark.slow
    def test_all_tracks_survive_save(self, temp_dir):
        """Test all 8 MIDI tracks survive save/load."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        for track_num in range(1, 9):
            pattern.midi_track(track_num).active_steps = [track_num, track_num + 8]

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        for track_num in range(1, 9):
            expected = [track_num, track_num + 8]
            assert loaded.bank(1).pattern(1).midi_track(track_num).active_steps == expected

    @pytest.mark.slow
    def test_cc_plocks_survive_save(self, temp_dir):
        """Test that CC p-locks survive save/load."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)

        midi_track.step(1).pitch_bend = 100
        midi_track.step(5).aftertouch = 80
        midi_track.step(9).set_cc(1, 64)
        midi_track.step(13).set_cc(5, 127)

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        loaded_track = loaded.bank(1).pattern(1).midi_track(1)
        assert loaded_track.step(1).pitch_bend == 100
        assert loaded_track.step(5).aftertouch == 80
        assert loaded_track.step(9).cc(1) == 64
        assert loaded_track.step(13).cc(5) == 127


# =============================================================================
# Flex Step Tests
# =============================================================================

class TestFlexStepType:
    """FlexStep type detection tests."""

    def test_flex_track_returns_flexstep(self):
        """Test that Flex machine tracks return FlexStep."""
        from octapy.api.step import FlexStep
        project = Project.from_template("TEST")
        # Must explicitly set machine type to Flex
        project.bank(1).part(1).track(1).machine_type = MachineType.FLEX
        step = project.bank(1).pattern(1).track(1).step(1)
        assert isinstance(step, FlexStep)

    def test_flexstep_has_sampler_properties(self):
        """Test that FlexStep inherits SamplerStep properties."""
        project = Project.from_template("TEST")
        project.bank(1).part(1).track(1).machine_type = MachineType.FLEX
        step = project.bank(1).pattern(1).track(1).step(1)
        # Should have volume, pitch, sample_lock from SamplerStep
        assert hasattr(step, 'volume')
        assert hasattr(step, 'pitch')
        assert hasattr(step, 'sample_lock')


class TestFlexStepLengthPlock:
    """FlexStep length p-lock tests."""

    def _setup_flex_track(self, project):
        """Configure track 1 as Flex machine."""
        project.bank(1).part(1).track(1).machine_type = MachineType.FLEX

    def test_length_default_none(self):
        """Test length p-lock defaults to None."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.length is None

    def test_set_length_full(self):
        """Test setting length to 1.0 (full sample)."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.length = 1.0
        assert step.length == 1.0

    def test_set_length_half(self):
        """Test setting length to 0.5 (half sample)."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.length = 0.5
        # Should quantize to nearest 0-127 value
        result = step.length
        assert 0.49 <= result <= 0.51  # Allow for quantization

    def test_set_length_zero(self):
        """Test setting length to 0.0."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.length = 0.0
        assert step.length == 0.0

    def test_set_length_quantization(self):
        """Test length values are quantized to 0-127."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        # 0.25 should quantize to 32/127 ≈ 0.252
        step.length = 0.25
        assert 0.24 <= step.length <= 0.26

    def test_clear_length(self):
        """Test clearing length p-lock."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.length = 0.5
        step.length = None
        assert step.length is None

    def test_length_clamps_above_one(self):
        """Test length values above 1.0 are clamped."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.length = 1.5
        assert step.length == 1.0

    def test_length_clamps_below_zero(self):
        """Test length values below 0.0 are clamped."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.length = -0.5
        assert step.length == 0.0


class TestFlexStepReversePlock:
    """FlexStep reverse p-lock tests."""

    def _setup_flex_track(self, project):
        """Configure track 1 as Flex machine."""
        project.bank(1).part(1).track(1).machine_type = MachineType.FLEX

    def test_reverse_default_none(self):
        """Test reverse p-lock defaults to None."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(1)
        assert step.reverse is None

    def test_set_reverse_true(self):
        """Test setting reverse to True."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.reverse = True
        assert step.reverse is True

    def test_set_reverse_false(self):
        """Test setting reverse to False."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.reverse = False
        assert step.reverse is False

    def test_clear_reverse(self):
        """Test clearing reverse p-lock."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.reverse = True
        step.reverse = None
        assert step.reverse is None

    def test_reverse_toggle(self):
        """Test toggling reverse back and forth."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        step = project.bank(1).pattern(1).track(1).step(5)

        step.reverse = True
        assert step.reverse is True

        step.reverse = False
        assert step.reverse is False

        step.reverse = True
        assert step.reverse is True


class TestFlexStepPlocksIndependent:
    """Test FlexStep p-locks are independent per step."""

    def _setup_flex_track(self, project):
        """Configure track 1 as Flex machine."""
        project.bank(1).part(1).track(1).machine_type = MachineType.FLEX

    def test_length_independent_per_step(self):
        """Test length p-locks are independent per step."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        track = project.bank(1).pattern(1).track(1)

        track.step(1).length = 0.25
        track.step(5).length = 0.5
        track.step(9).length = 0.75

        assert 0.24 <= track.step(1).length <= 0.26
        assert 0.49 <= track.step(5).length <= 0.51
        assert 0.74 <= track.step(9).length <= 0.76
        assert track.step(2).length is None

    def test_reverse_independent_per_step(self):
        """Test reverse p-locks are independent per step."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        track = project.bank(1).pattern(1).track(1)

        track.step(1).reverse = True
        track.step(5).reverse = False
        track.step(9).reverse = True

        assert track.step(1).reverse is True
        assert track.step(5).reverse is False
        assert track.step(9).reverse is True
        assert track.step(2).reverse is None


class TestFlexStepRoundTrip:
    """FlexStep p-lock round-trip tests."""

    def _setup_flex_track(self, project):
        """Configure track 1 as Flex machine."""
        project.bank(1).part(1).track(1).machine_type = MachineType.FLEX

    @pytest.mark.slow
    def test_length_survives_save(self, temp_dir):
        """Test length p-lock survives save/load."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        track = project.bank(1).pattern(1).track(1)

        track.step(5).length = 0.5

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        loaded_length = loaded.bank(1).pattern(1).track(1).step(5).length
        assert 0.49 <= loaded_length <= 0.51

    @pytest.mark.slow
    def test_reverse_survives_save(self, temp_dir):
        """Test reverse p-lock survives save/load."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        track = project.bank(1).pattern(1).track(1)

        track.step(5).reverse = True

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.bank(1).pattern(1).track(1).step(5).reverse is True

    @pytest.mark.slow
    def test_multiple_flex_plocks_survive_save(self, temp_dir):
        """Test multiple FlexStep p-locks survive save/load."""
        project = Project.from_template("TEST")
        self._setup_flex_track(project)
        track = project.bank(1).pattern(1).track(1)

        track.step(1).length = 0.25
        track.step(1).reverse = True
        track.step(5).length = 0.75
        track.step(5).reverse = False
        track.step(9).volume = 100  # Inherited from SamplerStep

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        loaded_track = loaded.bank(1).pattern(1).track(1)
        assert 0.24 <= loaded_track.step(1).length <= 0.26
        assert loaded_track.step(1).reverse is True
        assert 0.74 <= loaded_track.step(5).length <= 0.76
        assert loaded_track.step(5).reverse is False
        assert loaded_track.step(9).volume == 100
