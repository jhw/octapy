"""
Tests for auto slot management in Project class.
"""

import pytest

from octapy import Project, SlotLimitExceeded, InvalidSlotNumber


class TestSlotAutoAssignment:
    """Tests for automatic slot assignment."""

    def test_auto_assign_first_slot(self):
        """Test that first sample gets slot 1."""
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav")

        assert project.get_slot("../AUDIO/kick.wav") == 1

    def test_auto_assign_sequential_slots(self):
        """Test that samples get sequential slots."""
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav")
        project.add_sample("../AUDIO/snare.wav")
        project.add_sample("../AUDIO/hat.wav")

        assert project.get_slot("../AUDIO/kick.wav") == 1
        assert project.get_slot("../AUDIO/snare.wav") == 2
        assert project.get_slot("../AUDIO/hat.wav") == 3

    def test_reuse_slot_for_same_path(self):
        """Test that same path reuses existing slot."""
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav")
        project.add_sample("../AUDIO/snare.wav")
        project.add_sample("../AUDIO/kick.wav")  # Same as first

        # Should only have 2 unique slots
        assert project.flex_slot_count == 2
        assert project.get_slot("../AUDIO/kick.wav") == 1
        assert project.get_slot("../AUDIO/snare.wav") == 2

    def test_explicit_slot_assignment(self):
        """Test explicit slot assignment."""
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav", slot=5)

        assert project.get_slot("../AUDIO/kick.wav") == 5

    def test_mixed_auto_and_explicit(self):
        """Test mixing auto and explicit slot assignment."""
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav", slot=5)
        project.add_sample("../AUDIO/snare.wav")  # Auto-assign

        assert project.get_slot("../AUDIO/kick.wav") == 5
        assert project.get_slot("../AUDIO/snare.wav") == 1  # First available


class TestSlotTracking:
    """Tests for slot count tracking."""

    def test_flex_slot_count(self):
        """Test flex slot count property."""
        project = Project.from_template("TEST")
        assert project.flex_slot_count == 0

        project.add_sample("../AUDIO/kick.wav")
        assert project.flex_slot_count == 1

        project.add_sample("../AUDIO/snare.wav")
        assert project.flex_slot_count == 2

    def test_static_slot_count(self):
        """Test static slot count property."""
        project = Project.from_template("TEST")
        assert project.static_slot_count == 0

        project.add_sample("../AUDIO/kick.wav", slot_type="STATIC")
        assert project.static_slot_count == 1
        assert project.flex_slot_count == 0

    def test_flex_and_static_separate_pools(self):
        """Test that flex and static use separate slot pools."""
        project = Project.from_template("TEST")

        # Add flex sample
        project.add_sample("../AUDIO/kick.wav", slot_type="FLEX")

        # Add static sample - should get slot 1 (not 2)
        project.add_sample("../AUDIO/snare.wav", slot_type="STATIC")

        assert project.get_slot("../AUDIO/kick.wav", "FLEX") == 1
        assert project.get_slot("../AUDIO/snare.wav", "STATIC") == 1


class TestFlexCountUpdate:
    """Tests for automatic flex_count update."""

    def test_flex_count_auto_updated(self):
        """Test that bank flex_count is auto-updated."""
        project = Project.from_template("TEST")
        bank = project.bank(1)

        assert bank.flex_count == 0

        project.add_sample("../AUDIO/kick.wav")
        assert bank.flex_count == 1

        project.add_sample("../AUDIO/snare.wav")
        assert bank.flex_count == 2

    def test_flex_count_not_updated_for_static(self):
        """Test that static samples don't update flex_count."""
        project = Project.from_template("TEST")
        bank = project.bank(1)

        project.add_sample("../AUDIO/kick.wav", slot_type="STATIC")
        assert bank.flex_count == 0


class TestSlotExceptions:
    """Tests for slot-related exceptions."""

    def test_invalid_slot_number_zero(self):
        """Test that slot 0 raises InvalidSlotNumber."""
        project = Project.from_template("TEST")

        with pytest.raises(InvalidSlotNumber):
            project.add_sample("../AUDIO/kick.wav", slot=0)

    def test_invalid_slot_number_too_high(self):
        """Test that slot > 128 raises InvalidSlotNumber."""
        project = Project.from_template("TEST")

        with pytest.raises(InvalidSlotNumber):
            project.add_sample("../AUDIO/kick.wav", slot=129)

    def test_duplicate_slot_assignment(self):
        """Test that assigning to an occupied slot raises InvalidSlotNumber."""
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav", slot=1)

        with pytest.raises(InvalidSlotNumber):
            project.add_sample("../AUDIO/snare.wav", slot=1)


class TestSlotLoadFromDirectory:
    """Tests for slot tracking initialization from existing projects."""

    def test_slots_loaded_from_directory(self, temp_dir):
        """Test that slots are tracked when loading from directory."""
        # Create and save a project with samples
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav")
        project.add_sample("../AUDIO/snare.wav")
        project.to_directory(temp_dir / "TEST")

        # Load it back
        loaded = Project.from_directory(temp_dir / "TEST")

        # Slots should be tracked
        assert loaded.flex_slot_count == 2
        assert loaded.get_slot("../AUDIO/kick.wav") == 1
        assert loaded.get_slot("../AUDIO/snare.wav") == 2

    def test_new_samples_get_next_slot_after_load(self, temp_dir):
        """Test that new samples get sequential slots after load."""
        # Create and save a project with samples
        project = Project.from_template("TEST")
        project.add_sample("../AUDIO/kick.wav")
        project.add_sample("../AUDIO/snare.wav")
        project.to_directory(temp_dir / "TEST")

        # Load and add more samples
        loaded = Project.from_directory(temp_dir / "TEST")
        loaded.add_sample("../AUDIO/hat.wav")

        # Should get slot 3
        assert loaded.get_slot("../AUDIO/hat.wav") == 3
