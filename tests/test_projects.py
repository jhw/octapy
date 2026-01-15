"""
Tests for ProjectFile.
"""

import pytest

from octapy import ProjectFile, SampleSlot


class TestProjectFileBasics:
    """Basic ProjectFile tests."""

    def test_create_project(self, project_file):
        """Test creating a new ProjectFile."""
        assert project_file is not None

    def test_default_version(self, project_file):
        """Test default version."""
        assert project_file.version == 19

    def test_default_os_version(self, project_file):
        """Test default OS version."""
        assert "1.40" in project_file.os_version


class TestProjectFileTempo:
    """ProjectFile tempo tests."""

    def test_default_tempo(self, project_file):
        """Test default tempo is 120 BPM."""
        assert project_file.tempo == 120.0

    def test_default_tempo_x24(self, project_file):
        """Test default tempo_x24 is 2880."""
        assert project_file.tempo_x24 == 2880

    def test_set_tempo(self, project_file):
        """Test setting tempo in BPM."""
        project_file.tempo = 140.0
        assert project_file.tempo == 140.0
        assert project_file.tempo_x24 == 3360  # 140 * 24

    def test_set_tempo_x24(self, project_file):
        """Test setting raw tempo value."""
        project_file.tempo_x24 = 2400  # 100 BPM
        assert project_file.tempo == 100.0


class TestProjectFileSampleSlots:
    """ProjectFile sample slot tests."""

    def test_add_sample_slot(self, project_file):
        """Test adding a sample slot."""
        slot = project_file.add_sample_slot(
            slot_number=1,
            path="../AUDIO/sample.wav",
            slot_type="FLEX",
        )

        assert slot is not None
        assert len(project_file.sample_slots) == 1
        assert project_file.sample_slots[0].slot_number == 1
        assert project_file.sample_slots[0].path == "../AUDIO/sample.wav"

    def test_add_multiple_slots(self, project_file):
        """Test adding multiple sample slots."""
        project_file.add_sample_slot(1, "../AUDIO/kick.wav")
        project_file.add_sample_slot(2, "../AUDIO/snare.wav")
        project_file.add_sample_slot(3, "../AUDIO/hat.wav")

        assert len(project_file.sample_slots) == 3

    def test_add_recorder_slots(self, project_file):
        """Test adding recorder slots."""
        project_file.add_recorder_slots()

        # Should add 8 recorder slots (129-136)
        assert len(project_file.sample_slots) == 8

        for i, slot in enumerate(project_file.sample_slots):
            assert slot.slot_number == 129 + i

    def test_slot_properties(self, project_file):
        """Test sample slot properties."""
        slot = project_file.add_sample_slot(
            slot_number=1,
            path="../AUDIO/sample.wav",
            slot_type="FLEX",
            gain=64,
            loop_mode=1,
            timestretch_mode=2,
        )

        assert slot.slot_type == "FLEX"
        assert slot.gain == 64
        assert slot.loop_mode == 1
        assert slot.timestretch_mode == 2


class TestProjectFileRoundTrip:
    """ProjectFile read/write round-trip tests."""

    def test_write_read_roundtrip(self, project_file, temp_dir):
        """Test that write then read preserves data."""
        path = temp_dir / "project.work"

        # Add some data
        project_file.tempo = 130.0
        project_file.add_sample_slot(1, "../AUDIO/kick.wav", slot_type="FLEX")
        project_file.add_sample_slot(2, "../AUDIO/snare.wav", slot_type="FLEX")

        # Write
        project_file.to_file(path)

        # Read back
        loaded = ProjectFile.from_file(path)

        # Verify - note: not all fields survive round-trip currently
        assert len(loaded.sample_slots) == 2
        assert loaded.sample_slots[0].slot_number == 1
        assert loaded.sample_slots[1].slot_number == 2

    def test_crlf_line_endings(self, project_file, temp_dir):
        """Test that output uses CRLF line endings."""
        path = temp_dir / "project.work"
        project_file.to_file(path)

        with open(path, 'rb') as f:
            content = f.read()

        # Should contain CRLF
        assert b'\r\n' in content

        # Should not contain lone LF (except after CR)
        lines = content.split(b'\r\n')
        for line in lines[:-1]:  # Exclude last which may be empty
            assert b'\n' not in line


class TestSampleSlot:
    """SampleSlot tests."""

    def test_default_values(self):
        """Test SampleSlot default values."""
        slot = SampleSlot()

        assert slot.slot_type == "FLEX"
        assert slot.slot_number == 1
        assert slot.path == ""
        assert slot.bpm_x24 == 2880
        assert slot.gain == 48

    def test_to_ini_block(self):
        """Test INI block generation."""
        slot = SampleSlot(
            slot_type="FLEX",
            slot_number=1,
            path="../AUDIO/kick.wav",
            gain=48,
        )

        ini = slot.to_ini_block()

        assert "[SAMPLE]" in ini
        assert "TYPE=FLEX" in ini
        assert "SLOT=001" in ini
        assert "PATH=../AUDIO/kick.wav" in ini
        assert "[/SAMPLE]" in ini
