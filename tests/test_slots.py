"""
Tests for auto slot management in Project class.
"""

import pytest
from pathlib import Path

from octapy import Project, SlotLimitExceeded, InvalidSlotNumber


@pytest.fixture
def sample_files(temp_dir):
    """Create temporary WAV files for testing."""
    from pydub import AudioSegment

    files = {}
    for name in ["kick.wav", "snare.wav", "hat.wav"]:
        path = temp_dir / name
        # Create a short silent WAV file
        audio = AudioSegment.silent(duration=100)
        audio.export(str(path), format="wav")
        files[name] = path

    return files


class TestSlotAutoAssignment:
    """Tests for automatic slot assignment."""

    def test_auto_assign_first_slot(self, sample_files):
        """Test that first sample gets slot 1."""
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"])

        assert project.get_slot("kick.wav") == 1

    def test_auto_assign_sequential_slots(self, sample_files):
        """Test that samples get sequential slots."""
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"])
        project.add_sample(sample_files["snare.wav"])
        project.add_sample(sample_files["hat.wav"])

        assert project.get_slot("kick.wav") == 1
        assert project.get_slot("snare.wav") == 2
        assert project.get_slot("hat.wav") == 3

    def test_reuse_slot_for_same_file(self, sample_files):
        """Test that same file reuses existing slot."""
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"])
        project.add_sample(sample_files["snare.wav"])
        project.add_sample(sample_files["kick.wav"])  # Same as first

        # Should only have 2 unique slots
        assert project.flex_slot_count == 2
        assert project.get_slot("kick.wav") == 1
        assert project.get_slot("snare.wav") == 2

    def test_explicit_slot_assignment(self, sample_files):
        """Test explicit slot assignment."""
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"], slot=5)

        assert project.get_slot("kick.wav") == 5

    def test_mixed_auto_and_explicit(self, sample_files):
        """Test mixing auto and explicit slot assignment."""
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"], slot=5)
        project.add_sample(sample_files["snare.wav"])  # Auto-assign

        assert project.get_slot("kick.wav") == 5
        assert project.get_slot("snare.wav") == 1  # First available


class TestSlotMarkers:
    """Tests for markers set by add_sample."""

    def test_add_sample_sets_trim_end(self, sample_files):
        """Test that add_sample sets trim_end to sample length in markers."""
        project = Project.from_template("TEST")
        slot = project.add_sample(sample_files["kick.wav"])

        markers = project.markers.get_slot(slot)
        assert markers.sample_length > 0
        assert markers.trim_end == markers.sample_length

    def test_add_static_sample_sets_trim_end(self, sample_files):
        """Test that add_sample sets trim_end for static samples too."""
        project = Project.from_template("TEST")
        slot = project.add_sample(sample_files["kick.wav"], slot_type="STATIC")

        markers = project.markers.get_slot(slot, is_static=True)
        assert markers.sample_length > 0
        assert markers.trim_end == markers.sample_length


class TestSliceCount:
    """Tests for slice count stored in markers."""

    def test_set_slices_ms_sets_count(self, sample_files):
        """Test that set_slices_ms writes the slice count."""
        project = Project.from_template("TEST")
        slot = project.add_sample(sample_files["kick.wav"])

        markers = project.markers.get_slot(slot)
        markers.set_slices_ms([(0, 25), (25, 50), (50, 75), (75, 100)])
        project.markers.set_slot(slot, markers)

        result = project.markers.get_slot(slot)
        assert result.slice_count == 4

    def test_clear_all_slices_resets_count(self, sample_files):
        """Test that clearing slices zeros the count."""
        project = Project.from_template("TEST")
        slot = project.add_sample(sample_files["kick.wav"])

        markers = project.markers.get_slot(slot)
        markers.set_slices_ms([(0, 50), (50, 100)])
        markers.clear_all_slices()
        project.markers.set_slot(slot, markers)

        result = project.markers.get_slot(slot)
        assert result.slice_count == 0


class TestSlotTracking:
    """Tests for slot count tracking."""

    def test_flex_slot_count(self, sample_files):
        """Test flex slot count property."""
        project = Project.from_template("TEST")
        assert project.flex_slot_count == 0

        project.add_sample(sample_files["kick.wav"])
        assert project.flex_slot_count == 1

        project.add_sample(sample_files["snare.wav"])
        assert project.flex_slot_count == 2

    def test_static_slot_count(self, sample_files):
        """Test static slot count property."""
        project = Project.from_template("TEST")
        assert project.static_slot_count == 0

        project.add_sample(sample_files["kick.wav"], slot_type="STATIC")
        assert project.static_slot_count == 1
        assert project.flex_slot_count == 0

    def test_flex_and_static_separate_pools(self, sample_files):
        """Test that flex and static use separate slot pools."""
        project = Project.from_template("TEST")

        # Add flex sample
        project.add_sample(sample_files["kick.wav"], slot_type="FLEX")

        # Add static sample - should get slot 1 (not 2)
        project.add_sample(sample_files["snare.wav"], slot_type="STATIC")

        assert project.get_slot("kick.wav", "FLEX") == 1
        assert project.get_slot("snare.wav", "STATIC") == 1


class TestFlexCountUpdate:
    """Tests for automatic flex_count update."""

    def test_flex_count_auto_updated(self, sample_files):
        """Test that bank flex_count is auto-updated."""
        project = Project.from_template("TEST")
        bank = project.bank(1)

        assert bank.flex_count == 0

        project.add_sample(sample_files["kick.wav"])
        assert bank.flex_count == 1

        project.add_sample(sample_files["snare.wav"])
        assert bank.flex_count == 2

    def test_flex_count_not_updated_for_static(self, sample_files):
        """Test that static samples don't update flex_count."""
        project = Project.from_template("TEST")
        bank = project.bank(1)

        project.add_sample(sample_files["kick.wav"], slot_type="STATIC")
        assert bank.flex_count == 0


class TestSlotExceptions:
    """Tests for slot-related exceptions."""

    def test_invalid_slot_number_zero(self, sample_files):
        """Test that slot 0 raises InvalidSlotNumber."""
        project = Project.from_template("TEST")

        with pytest.raises(InvalidSlotNumber):
            project.add_sample(sample_files["kick.wav"], slot=0)

    def test_invalid_slot_number_too_high(self, sample_files):
        """Test that slot > 128 raises InvalidSlotNumber."""
        project = Project.from_template("TEST")

        with pytest.raises(InvalidSlotNumber):
            project.add_sample(sample_files["kick.wav"], slot=129)

    def test_duplicate_slot_assignment(self, sample_files):
        """Test that assigning to an occupied slot raises InvalidSlotNumber."""
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"], slot=1)

        with pytest.raises(InvalidSlotNumber):
            project.add_sample(sample_files["snare.wav"], slot=1)


@pytest.mark.slow
class TestSlotLoadFromDirectory:
    """Tests for slot tracking initialization from existing projects."""

    def test_slots_loaded_from_directory(self, temp_dir, sample_files):
        """Test that slots are tracked when loading from directory."""
        # Create and save a project with samples
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"])
        project.add_sample(sample_files["snare.wav"])
        project.to_directory(temp_dir / "TEST")

        # Load it back
        loaded = Project.from_directory(temp_dir / "TEST")

        # Slots should be tracked
        assert loaded.flex_slot_count == 2

    def test_new_samples_get_next_slot_after_load(self, temp_dir, sample_files):
        """Test that new samples get sequential slots after load."""
        # Create and save a project with samples
        project = Project.from_template("TEST")
        project.add_sample(sample_files["kick.wav"])
        project.add_sample(sample_files["snare.wav"])
        project.to_directory(temp_dir / "TEST")

        # Load and add more samples
        loaded = Project.from_directory(temp_dir / "TEST")
        loaded.add_sample(sample_files["hat.wav"])

        # Should get slot 3
        assert loaded.get_slot("hat.wav") == 3
