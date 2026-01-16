"""
Tests for Pattern, PatternTrack, and Step high-level API.
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


class TestPatternTrack:
    """PatternTrack (sequence data) tests."""

    def test_get_pattern_track(self):
        """Test getting a PatternTrack."""
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


class TestStep:
    """Step (individual step) tests."""

    def test_get_step(self):
        """Test getting a Step."""
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
        """Test that Step.active matches active_steps list."""
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

    def test_probability_survives_save(self, temp_dir):
        """Test that probability survives save/load."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)

        track.step(5).probability = 0.5

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.bank(1).pattern(1).track(1).step(5).probability == 0.5
