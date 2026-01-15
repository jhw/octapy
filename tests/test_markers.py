"""
Tests for MarkersFile.
"""

import pytest

from octapy import MarkersFile
from octapy.api.markers import (
    MARKERS_HEADER,
    MARKERS_FILE_VERSION,
    NUM_FLEX_SLOTS,
    NUM_STATIC_SLOTS,
    SLOT_SIZE,
)


class TestMarkersFileBasics:
    """Basic MarkersFile tests."""

    def test_new_from_template(self, markers_file):
        """Test creating a new markers file from template."""
        assert markers_file is not None

    def test_header_valid(self, markers_file):
        """Test that template has correct header."""
        assert markers_file.check_header() is True
        assert markers_file.header == MARKERS_HEADER

    def test_version_valid(self, markers_file):
        """Test that template has correct version."""
        assert markers_file.check_version() is True
        assert markers_file.version == MARKERS_FILE_VERSION


class TestMarkersFileRoundTrip:
    """Read/write round-trip tests."""

    def test_write_read_roundtrip(self, markers_file, temp_dir):
        """Test that write then read produces identical data."""
        path = temp_dir / "markers.work"

        # Write to file
        markers_file.to_file(path)

        # Read back
        loaded = MarkersFile.from_file(path)

        # Compare
        assert loaded.header == markers_file.header
        assert loaded.version == markers_file.version
        assert loaded._data == markers_file._data

    def test_checksum_updates_on_write(self, markers_file, temp_dir):
        """Test that checksum is recalculated on write."""
        path = temp_dir / "markers.work"

        # Modify something
        markers_file.set_sample_length(slot=1, length=44100)

        # Write (should update checksum)
        markers_file.to_file(path)

        # Read back and verify checksum
        loaded = MarkersFile.from_file(path)
        assert loaded.verify_checksum() is True


class TestMarkersFileSampleLength:
    """Sample length tests."""

    def test_set_sample_length_flex(self, markers_file):
        """Test setting flex slot sample length."""
        markers_file.set_sample_length(slot=1, length=44100)
        assert markers_file.get_sample_length(slot=1) == 44100

    def test_set_sample_length_static(self, markers_file):
        """Test setting static slot sample length."""
        markers_file.set_sample_length(slot=1, length=88200, is_static=True)
        assert markers_file.get_sample_length(slot=1, is_static=True) == 88200

    def test_set_sample_length_large(self, markers_file):
        """Test setting large sample length (32-bit value)."""
        large_length = 10_000_000  # ~3.7 minutes at 44.1kHz
        markers_file.set_sample_length(slot=1, length=large_length)
        assert markers_file.get_sample_length(slot=1) == large_length

    def test_set_sample_length_multiple_slots(self, markers_file):
        """Test setting sample lengths on multiple slots."""
        lengths = {1: 44100, 2: 88200, 3: 132300, 4: 22050}

        for slot, length in lengths.items():
            markers_file.set_sample_length(slot=slot, length=length)

        for slot, expected in lengths.items():
            assert markers_file.get_sample_length(slot=slot) == expected


class TestMarkersFileSlotAccess:
    """Slot access tests."""

    def test_get_slot_flex(self, markers_file):
        """Test getting a flex slot."""
        slot = markers_file.get_slot(1)
        assert slot is not None

    def test_get_slot_static(self, markers_file):
        """Test getting a static slot."""
        slot = markers_file.get_slot(1, is_static=True)
        assert slot is not None

    def test_slot_properties(self, markers_file):
        """Test slot marker properties."""
        slot = markers_file.get_slot(1)

        # Set properties
        slot.sample_length = 44100
        slot.trim_start = 0
        slot.trim_end = 44100
        slot.loop_point = 22050

        # Verify
        assert slot.sample_length == 44100
        assert slot.trim_start == 0
        assert slot.trim_end == 44100
        assert slot.loop_point == 22050


class TestMarkersFileChecksum:
    """Checksum tests."""

    def test_checksum_calculation(self, markers_file):
        """Test that checksum can be calculated."""
        checksum = markers_file.calculate_checksum()
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 65535  # 16-bit checksum

    def test_checksum_verification(self, markers_file):
        """Test checksum verification on template."""
        markers_file.update_checksum()
        assert markers_file.verify_checksum() is True
