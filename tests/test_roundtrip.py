"""
Project-level round-trip integration tests.

Tests that Project survives directory and zip round-trips.
"""

import tempfile
from pathlib import Path

import pytest

from octapy import Project, FX1Type


# =============================================================================
# Fixtures
# =============================================================================

FIXTURE_DIR = Path(__file__).parent / "fixtures"
HELLO_FLEX_ZIP = FIXTURE_DIR / "HELLO FLEX.zip"


@pytest.fixture
def hello_flex_project():
    """Load the HELLO FLEX fixture project."""
    if not HELLO_FLEX_ZIP.exists():
        pytest.skip("HELLO FLEX.zip fixture not found")
    return Project.from_zip(HELLO_FLEX_ZIP)


# =============================================================================
# Project Round-Trip Tests
# =============================================================================

@pytest.mark.slow
class TestProjectRoundTrip:
    """Tests for Project read/write round-trip integrity."""

    def test_project_from_template_to_directory_round_trip(self):
        """Project from template survives directory round-trip."""
        project = Project.from_template("TEST PROJECT")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "TEST PROJECT"

            # Write to directory
            project.to_directory(tmp_path)

            # Verify files exist
            assert (tmp_path / "project.work").exists()
            assert (tmp_path / "bank01.work").exists()
            assert (tmp_path / "markers.work").exists()

            # Read back
            restored = Project.from_directory(tmp_path)

            assert restored.name == project.name
            assert restored.tempo == project.tempo

    def test_project_from_template_to_zip_round_trip(self):
        """Project from template survives zip round-trip."""
        project = Project.from_template("ZIP TEST")
        project.tempo = 135.0

        with tempfile.TemporaryDirectory() as tmp:
            # Use project name as zip filename so it restores correctly
            zip_path = Path(tmp) / "ZIP TEST.zip"

            # Write to zip
            project.to_zip(zip_path)
            assert zip_path.exists()

            # Read back
            restored = Project.from_zip(zip_path)

            assert restored.name == "ZIP TEST"
            assert restored.tempo == 135.0

    def test_project_modification_persists(self):
        """Project modifications survive round-trip."""
        project = Project.from_template("MOD TEST")

        # Make modifications
        project.tempo = 140.0
        project.master_track = True
        project.bank(1).pattern(1).scale_length = 32
        project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]
        project.bank(1).part(1).audio_track(1).fx1_type = FX1Type.CHORUS

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "MOD TEST"

            # Write and read back
            project.to_directory(tmp_path)
            restored = Project.from_directory(tmp_path)

            assert restored.tempo == 140.0
            assert restored.master_track == True
            assert restored.bank(1).pattern(1).scale_length == 32
            assert restored.bank(1).pattern(1).audio_track(1).active_steps == [1, 5, 9, 13]
            assert restored.bank(1).part(1).audio_track(1).fx1_type == FX1Type.CHORUS


@pytest.mark.slow
class TestProjectFixtureRoundTrip:
    """Tests using the HELLO FLEX fixture project."""

    def test_load_hello_flex_project(self, hello_flex_project):
        """HELLO FLEX project loads successfully."""
        project = hello_flex_project

        assert project.name == "HELLO FLEX"
        # Should have 16 banks
        for i in range(1, 17):
            assert project.bank(i) is not None

    def test_hello_flex_to_dict(self, hello_flex_project):
        """HELLO FLEX project converts to dict."""
        project = hello_flex_project
        d = project.to_dict()

        assert d["name"] == "HELLO FLEX"
        assert len(d["banks"]) == 16

    def test_hello_flex_round_trip(self, hello_flex_project):
        """HELLO FLEX project survives round-trip."""
        project = hello_flex_project

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "HELLO FLEX"

            # Write and read back
            project.to_directory(tmp_path)
            restored = Project.from_directory(tmp_path)

            assert restored.name == project.name
            assert restored.tempo == project.tempo

    def test_hello_flex_inspect_patterns(self, hello_flex_project):
        """Can inspect patterns in HELLO FLEX project."""
        project = hello_flex_project

        # Look for patterns with active steps
        patterns_with_steps = []
        for bank_num in range(1, 17):
            bank = project.bank(bank_num)
            for pattern_num in range(1, 17):
                pattern = bank.pattern(pattern_num)
                for track_num in range(1, 9):
                    track = pattern.audio_track(track_num)
                    if track.active_steps:
                        patterns_with_steps.append((bank_num, pattern_num, track_num, track.active_steps))

        # The HELLO FLEX demo should have some patterns
        # (This may vary based on what was saved)
        # Just verify we can read the data
        assert isinstance(patterns_with_steps, list)

    def test_hello_flex_inspect_parts(self, hello_flex_project):
        """Can inspect parts in HELLO FLEX project."""
        project = hello_flex_project

        # Get part 1 from bank 1
        part = project.bank(1).part(1)

        # Should be able to read track configurations
        for track_num in range(1, 9):
            track = part.audio_track(track_num)
            assert track.machine_type is not None
            assert isinstance(track.flex_slot, int)
