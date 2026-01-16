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
