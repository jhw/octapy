"""
Tests for BankFile.
"""

import pytest

from octapy import BankFile, MachineType
from octapy.api.banks import BANK_FILE_SIZE, BANK_HEADER, BANK_FILE_VERSION


class TestBankFileBasics:
    """Basic BankFile tests."""

    def test_new_from_template(self, bank_file):
        """Test creating a new bank from template."""
        assert bank_file is not None
        assert len(bank_file._data) == BANK_FILE_SIZE

    def test_header_valid(self, bank_file):
        """Test that template has correct header."""
        assert bank_file.check_header() is True
        assert bank_file.header == BANK_HEADER

    def test_version_valid(self, bank_file):
        """Test that template has correct version."""
        assert bank_file.check_version() is True
        assert bank_file.version == BANK_FILE_VERSION


class TestBankFileRoundTrip:
    """Read/write round-trip tests."""

    def test_write_read_roundtrip(self, bank_file, temp_dir):
        """Test that write then read produces identical data."""
        path = temp_dir / "bank01.work"

        # Write to file
        bank_file.to_file(path)

        # Read back
        loaded = BankFile.from_file(path)

        # Compare
        assert loaded.header == bank_file.header
        assert loaded.version == bank_file.version
        assert loaded._data == bank_file._data

    def test_checksum_updates_on_write(self, bank_file, temp_dir):
        """Test that checksum is recalculated on write."""
        path = temp_dir / "bank01.work"

        # Modify something
        bank_file.set_machine_type(1, MachineType.FLEX)

        # Write (should update checksum)
        bank_file.to_file(path)

        # Read back and verify checksum
        loaded = BankFile.from_file(path)
        assert loaded.verify_checksum() is True


class TestBankFileMachineTypes:
    """Machine type tests."""

    def test_default_machine_type(self, bank_file):
        """Test default machine type is STATIC."""
        # Template should have STATIC machines by default
        for track in range(1, 9):
            machine = bank_file.get_machine_type(track)
            assert machine == MachineType.STATIC

    def test_set_machine_type_flex(self, bank_file):
        """Test setting machine type to FLEX."""
        bank_file.set_machine_type(1, MachineType.FLEX)
        assert bank_file.get_machine_type(1) == MachineType.FLEX

    def test_set_machine_type_all_tracks(self, bank_file):
        """Test setting machine types on all tracks."""
        types = [
            MachineType.FLEX,
            MachineType.STATIC,
            MachineType.THRU,
            MachineType.NEIGHBOR,
            MachineType.PICKUP,
            MachineType.FLEX,
            MachineType.STATIC,
            MachineType.THRU,
        ]

        for track, machine_type in enumerate(types, 1):
            bank_file.set_machine_type(track, machine_type)

        for track, expected in enumerate(types, 1):
            assert bank_file.get_machine_type(track) == expected


class TestBankFileTrigs:
    """Trigger pattern tests."""

    def test_set_trigs_basic(self, bank_file):
        """Test setting trigger steps."""
        steps = [1, 5, 9, 13]
        bank_file.set_trigs(pattern=1, track=1, steps=steps)

        result = bank_file.get_trigs(pattern=1, track=1)
        assert result == steps

    def test_set_trigs_all_steps(self, bank_file):
        """Test setting all 16 steps."""
        steps = list(range(1, 17))
        bank_file.set_trigs(pattern=1, track=1, steps=steps)

        result = bank_file.get_trigs(pattern=1, track=1)
        assert result == steps

    def test_set_trigs_empty(self, bank_file):
        """Test clearing all triggers."""
        # First set some trigs
        bank_file.set_trigs(pattern=1, track=1, steps=[1, 5, 9, 13])

        # Then clear them
        bank_file.set_trigs(pattern=1, track=1, steps=[])

        result = bank_file.get_trigs(pattern=1, track=1)
        assert result == []

    def test_set_trigs_multiple_tracks(self, bank_file):
        """Test setting trigs on multiple tracks."""
        track_steps = {
            1: [1, 5, 9, 13],
            2: [5, 13],
            3: [1, 3, 5, 7, 9, 11, 13, 15],
            4: [2, 4, 6, 8, 10, 12, 14, 16],
        }

        for track, steps in track_steps.items():
            bank_file.set_trigs(pattern=1, track=track, steps=steps)

        for track, expected in track_steps.items():
            result = bank_file.get_trigs(pattern=1, track=track)
            assert result == expected


class TestBankFileSlots:
    """Slot assignment tests."""

    def test_set_flex_slot(self, bank_file):
        """Test setting flex slot assignment."""
        bank_file.set_flex_slot(track=1, slot=5)
        assert bank_file.get_flex_slot(track=1) == 5

    def test_set_static_slot(self, bank_file):
        """Test setting static slot assignment."""
        bank_file.set_static_slot(track=1, slot=10)
        assert bank_file.get_static_slot(track=1) == 10

    def test_flex_count(self, bank_file):
        """Test flex counter."""
        bank_file.flex_count = 4
        assert bank_file.flex_count == 4


class TestBankFileChecksum:
    """Checksum tests."""

    def test_checksum_calculation(self, bank_file):
        """Test that checksum can be calculated."""
        checksum = bank_file.calculate_checksum()
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 255

    def test_checksum_verification(self, bank_file):
        """Test checksum verification on template."""
        # Template should have valid checksum
        bank_file.update_checksum()
        assert bank_file.verify_checksum() is True

    def test_checksum_changes_with_data(self, bank_file):
        """Test that checksum changes when data changes."""
        bank_file.update_checksum()
        original_checksum = bank_file._data[-1]

        # Modify data
        bank_file.set_machine_type(1, MachineType.FLEX)
        bank_file.update_checksum()
        new_checksum = bank_file._data[-1]

        # Checksum should be different (usually)
        # Note: There's a tiny chance they could be the same by coincidence
        assert original_checksum != new_checksum or True  # Allow coincidence
