"""
Tests for Pattern and AudioTrack.
"""

import pytest

from octapy import BankFile, Pattern, AudioTrack
from octapy.api.patterns import PATTERN_SIZE, AUDIO_TRACK_SIZE, PATTERN_HEADER


class TestPatternBasics:
    """Basic Pattern tests."""

    def test_pattern_from_bank(self, bank_file):
        """Test getting a pattern from a bank."""
        pattern = bank_file.get_pattern(1)
        assert pattern is not None

    def test_pattern_header(self, bank_file):
        """Test pattern has correct header."""
        pattern = bank_file.get_pattern(1)
        assert pattern.check_header() is True

    def test_pattern_count(self, bank_file):
        """Test bank has 16 patterns."""
        patterns = bank_file.patterns
        assert len(patterns) == 16


class TestPatternTrigSteps:
    """Pattern trigger step tests."""

    def test_get_trigger_steps_empty(self, bank_file):
        """Test getting trigger steps when none are set."""
        pattern = bank_file.get_pattern(1)
        steps = pattern.get_trigger_steps(track=1)
        # Template may have empty trigs
        assert isinstance(steps, list)

    def test_set_trigger_steps(self, bank_file):
        """Test setting trigger steps."""
        pattern = bank_file.get_pattern(1)

        steps = [1, 5, 9, 13]
        pattern.set_trigger_steps(track=1, steps=steps)

        result = pattern.get_trigger_steps(track=1)
        assert result == steps

    def test_set_trigger_steps_all(self, bank_file):
        """Test setting all 16 trigger steps."""
        pattern = bank_file.get_pattern(1)

        steps = list(range(1, 17))
        pattern.set_trigger_steps(track=1, steps=steps)

        result = pattern.get_trigger_steps(track=1)
        assert result == steps

    def test_set_trigger_steps_extended(self, bank_file):
        """Test setting extended trigger steps (17-64)."""
        pattern = bank_file.get_pattern(1)

        # Steps in pages 2-4
        steps = [17, 33, 49, 64]
        pattern.set_trigger_steps(track=1, steps=steps)

        result = pattern.get_trigger_steps(track=1)
        assert result == steps

    def test_clear_trigger_steps(self, bank_file):
        """Test clearing trigger steps."""
        pattern = bank_file.get_pattern(1)

        # Set some steps
        pattern.set_trigger_steps(track=1, steps=[1, 5, 9, 13])

        # Clear them
        pattern.set_trigger_steps(track=1, steps=[])

        result = pattern.get_trigger_steps(track=1)
        assert result == []


class TestAudioTrack:
    """AudioTrack tests."""

    def test_get_audio_track(self, bank_file):
        """Test getting an audio track from a pattern."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)
        assert track is not None

    def test_audio_track_header(self, bank_file):
        """Test audio track has correct header."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)
        assert track.check_header() is True

    def test_all_audio_tracks(self, bank_file):
        """Test all 8 audio tracks are accessible."""
        pattern = bank_file.get_pattern(1)

        for track_num in range(1, 9):
            track = pattern.get_audio_track(track_num)
            assert track is not None
            assert track.check_header() is True


class TestPatternMultipleTracks:
    """Tests for multiple tracks in a pattern."""

    def test_independent_track_trigs(self, bank_file):
        """Test that tracks have independent trigger data."""
        pattern = bank_file.get_pattern(1)

        # Set different steps on each track
        track_steps = {
            1: [1, 5, 9, 13],
            2: [5, 13],
            3: [1, 2, 3, 4],
            4: [9, 10, 11, 12],
        }

        for track, steps in track_steps.items():
            pattern.set_trigger_steps(track=track, steps=steps)

        # Verify each track has its own steps
        for track, expected in track_steps.items():
            result = pattern.get_trigger_steps(track=track)
            assert result == expected, f"Track {track} mismatch"


class TestPatternRoundTrip:
    """Pattern read/write round-trip tests."""

    def test_pattern_survives_bank_save(self, bank_file, temp_dir):
        """Test that pattern data survives bank save/load."""
        # Set some pattern data
        bank_file.set_trigs(pattern=1, track=1, steps=[1, 5, 9, 13])
        bank_file.set_trigs(pattern=1, track=2, steps=[5, 13])

        # Save and reload
        path = temp_dir / "bank01.work"
        bank_file.to_file(path)
        loaded = BankFile.from_file(path)

        # Verify
        assert loaded.get_trigs(pattern=1, track=1) == [1, 5, 9, 13]
        assert loaded.get_trigs(pattern=1, track=2) == [5, 13]
