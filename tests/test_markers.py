"""
Tests for MarkersFile and slice functionality.
"""

import pytest

from octapy._io import (
    MarkersFile,
    Slice,
    MARKERS_HEADER,
    MARKERS_FILE_VERSION,
    NUM_FLEX_SLOTS,
    NUM_STATIC_SLOTS,
    SLOT_SIZE,
    NUM_SLICES,
    SLICE_LOOP_DISABLED,
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


# =============================================================================
# Slice Tests
# =============================================================================


class TestSliceDataclass:
    """Tests for Slice dataclass."""

    def test_create_basic_slice(self):
        """Test creating a basic slice."""
        s = Slice(trim_start=0, trim_end=44100)
        assert s.trim_start == 0
        assert s.trim_end == 44100
        assert s.loop_start is None

    def test_create_slice_with_loop(self):
        """Test creating a slice with loop point."""
        s = Slice(trim_start=0, trim_end=44100, loop_start=22050)
        assert s.trim_start == 0
        assert s.trim_end == 44100
        assert s.loop_start == 22050

    def test_slice_validation_negative_start(self):
        """Test that negative trim_start raises error."""
        with pytest.raises(ValueError, match="trim_start must be >= 0"):
            Slice(trim_start=-1, trim_end=100)

    def test_slice_validation_end_before_start(self):
        """Test that trim_end < trim_start raises error."""
        with pytest.raises(ValueError, match="trim_end.*must be >= trim_start"):
            Slice(trim_start=100, trim_end=50)

    def test_slice_validation_loop_before_start(self):
        """Test that loop_start < trim_start raises error."""
        with pytest.raises(ValueError, match="loop_start.*must be >= trim_start"):
            Slice(trim_start=100, trim_end=200, loop_start=50)

    def test_slice_validation_loop_at_end(self):
        """Test that loop_start >= trim_end raises error."""
        with pytest.raises(ValueError, match="loop_start.*must be < trim_end"):
            Slice(trim_start=100, trim_end=200, loop_start=200)

    def test_slice_is_empty(self):
        """Test is_empty property."""
        empty = Slice(trim_start=0, trim_end=0)
        assert empty.is_empty is True

        non_empty = Slice(trim_start=0, trim_end=100)
        assert non_empty.is_empty is False

    def test_slice_to_raw(self):
        """Test converting slice to raw values."""
        s = Slice(trim_start=100, trim_end=200, loop_start=150)
        raw = s.to_raw()
        assert raw == (100, 200, 150)

        # None loop should become SLICE_LOOP_DISABLED
        s2 = Slice(trim_start=100, trim_end=200)
        raw2 = s2.to_raw()
        assert raw2 == (100, 200, SLICE_LOOP_DISABLED)

    def test_slice_from_raw(self):
        """Test creating slice from raw values."""
        s = Slice.from_raw(100, 200, 150)
        assert s.trim_start == 100
        assert s.trim_end == 200
        assert s.loop_start == 150

        # SLICE_LOOP_DISABLED should become None
        s2 = Slice.from_raw(100, 200, SLICE_LOOP_DISABLED)
        assert s2.loop_start is None


class TestSlotMarkersSliceRaw:
    """Tests for raw slice access (in audio samples)."""

    def test_get_slice_empty(self, markers_file):
        """Test getting an empty slice."""
        slot = markers_file.get_slot(1)
        s = slot.get_slice(0)
        assert s.is_empty is True

    def test_set_get_slice(self, markers_file):
        """Test setting and getting a slice."""
        slot = markers_file.get_slot(1)
        slot.set_slice(0, trim_start=0, trim_end=44100)

        s = slot.get_slice(0)
        assert s.trim_start == 0
        assert s.trim_end == 44100
        assert s.loop_start is None

    def test_set_slice_with_loop(self, markers_file):
        """Test setting a slice with loop point."""
        slot = markers_file.get_slot(1)
        slot.set_slice(0, trim_start=0, trim_end=44100, loop_start=22050)

        s = slot.get_slice(0)
        assert s.loop_start == 22050

    def test_set_slice_multiple(self, markers_file):
        """Test setting multiple slices."""
        slot = markers_file.get_slot(1)

        # Set 4 slices (1 second each at 44.1kHz)
        for i in range(4):
            start = i * 44100
            end = (i + 1) * 44100
            slot.set_slice(i, trim_start=start, trim_end=end)

        # Verify
        for i in range(4):
            s = slot.get_slice(i)
            assert s.trim_start == i * 44100
            assert s.trim_end == (i + 1) * 44100

    def test_set_slice_index_bounds(self, markers_file):
        """Test slice index bounds checking."""
        slot = markers_file.get_slot(1)

        with pytest.raises(IndexError, match="Slice index must be 0-63"):
            slot.get_slice(-1)

        with pytest.raises(IndexError, match="Slice index must be 0-63"):
            slot.get_slice(64)

    def test_clear_slice(self, markers_file):
        """Test clearing a slice."""
        slot = markers_file.get_slot(1)

        # Set then clear
        slot.set_slice(0, trim_start=0, trim_end=44100)
        slot.clear_slice(0)

        s = slot.get_slice(0)
        assert s.is_empty is True

    def test_clear_all_slices(self, markers_file):
        """Test clearing all slices."""
        slot = markers_file.get_slot(1)

        # Set multiple slices
        for i in range(4):
            slot.set_slice(i, trim_start=i * 1000, trim_end=(i + 1) * 1000)

        # Clear all
        slot.clear_all_slices()

        # Verify all are empty
        for i in range(4):
            assert slot.get_slice(i).is_empty is True

    def test_slice_count(self, markers_file):
        """Test stored slice count property."""
        slot = markers_file.get_slot(1)
        assert slot.slice_count == 0

        # Stored count is set explicitly
        slot.slice_count = 4
        assert slot.slice_count == 4

        # Clear resets to 0
        slot.clear_all_slices()
        assert slot.slice_count == 0

    def test_get_all_slices(self, markers_file):
        """Test getting all non-empty slices."""
        slot = markers_file.get_slot(1)

        # Set some slices with gaps
        slot.set_slice(0, 0, 1000)
        slot.set_slice(2, 2000, 3000)  # Skip index 1
        slot.set_slice(5, 5000, 6000)  # Skip indices 3, 4

        slices = slot.get_all_slices()
        assert len(slices) == 3
        assert slices[0].trim_start == 0
        assert slices[1].trim_start == 2000
        assert slices[2].trim_start == 5000


class TestSlotMarkersSliceMilliseconds:
    """Tests for millisecond slice access."""

    def test_samples_to_ms_conversion(self, markers_file):
        """Test sample to ms conversion."""
        slot = markers_file.get_slot(1)

        # 44100 samples at 44.1kHz = 1000ms
        ms = slot._samples_to_ms(44100, 44100)
        assert ms == 1000

        # 22050 samples at 44.1kHz = 500ms
        ms = slot._samples_to_ms(22050, 44100)
        assert ms == 500

    def test_ms_to_samples_conversion(self, markers_file):
        """Test ms to sample conversion."""
        slot = markers_file.get_slot(1)

        # 1000ms at 44.1kHz = 44100 samples
        samples = slot._ms_to_samples(1000, 44100)
        assert samples == 44100

        # 500ms at 44.1kHz = 22050 samples
        samples = slot._ms_to_samples(500, 44100)
        assert samples == 22050

    def test_set_get_slice_ms(self, markers_file):
        """Test setting and getting slices in milliseconds."""
        slot = markers_file.get_slot(1)

        # Set slice: 0-1000ms
        slot.set_slice_ms(0, start_ms=0, end_ms=1000, sample_rate=44100)

        # Get in ms
        start, end, loop = slot.get_slice_ms(0, sample_rate=44100)
        assert start == 0
        assert end == 1000
        assert loop is None

        # Verify raw values
        s = slot.get_slice(0)
        assert s.trim_start == 0
        assert s.trim_end == 44100  # 1000ms at 44.1kHz

    def test_set_slice_ms_with_loop(self, markers_file):
        """Test setting slice with loop point in milliseconds."""
        slot = markers_file.get_slot(1)

        slot.set_slice_ms(0, start_ms=0, end_ms=1000, loop_ms=500, sample_rate=44100)

        start, end, loop = slot.get_slice_ms(0, sample_rate=44100)
        assert loop == 500

    def test_set_slices_ms_bulk(self, markers_file):
        """Test bulk setting slices in milliseconds."""
        slot = markers_file.get_slot(1)

        # Create 4 equal 250ms slices for a 1-second sample
        slot.set_slices_ms([
            (0, 250),
            (250, 500),
            (500, 750),
            (750, 1000),
        ], sample_rate=44100)

        # Verify
        assert slot.slice_count == 4

        slices = slot.get_all_slices_ms(sample_rate=44100)
        assert len(slices) == 4
        assert slices[0] == (0, 250, None)
        assert slices[1] == (250, 500, None)
        assert slices[2] == (500, 750, None)
        assert slices[3] == (750, 1000, None)

    def test_set_slices_ms_clears_existing(self, markers_file):
        """Test that set_slices_ms clears existing slices."""
        slot = markers_file.get_slot(1)

        # Set 8 slices
        slot.set_slices_ms([(i * 100, (i + 1) * 100) for i in range(8)])
        assert slot.slice_count == 8

        # Replace with 2 slices
        slot.set_slices_ms([(0, 500), (500, 1000)])
        assert slot.slice_count == 2

    def test_set_slices_ms_max_limit(self, markers_file):
        """Test that set_slices_ms enforces max 63 slices."""
        slot = markers_file.get_slot(1)

        # Try to set 65 slices
        with pytest.raises(ValueError, match="Maximum 63 slices"):
            slot.set_slices_ms([(i, i + 1) for i in range(65)])

    def test_different_sample_rates(self, markers_file):
        """Test slice operations with different sample rates."""
        slot = markers_file.get_slot(1)

        # Set at 48kHz
        slot.set_slice_ms(0, start_ms=0, end_ms=1000, sample_rate=48000)

        # Raw values should be 48000 samples
        s = slot.get_slice(0)
        assert s.trim_end == 48000

        # Get at 48kHz should give back 1000ms
        start, end, loop = slot.get_slice_ms(0, sample_rate=48000)
        assert end == 1000


class TestSliceRoundTrip:
    """Round-trip tests for slice data."""

    def test_slice_roundtrip_write_read(self, markers_file, temp_dir):
        """Test that slices survive write/read cycle."""
        slot = markers_file.get_slot(1)

        # Set some slices
        slot.set_slices_ms([
            (0, 250),
            (250, 500),
            (500, 750),
            (750, 1000),
        ], sample_rate=44100)

        # Write slot back to markers file (get_slot returns a copy)
        markers_file.set_slot(1, slot)

        # Write to file
        path = temp_dir / "markers.work"
        markers_file.to_file(path)

        # Read back
        loaded = MarkersFile.from_file(path)
        loaded_slot = loaded.get_slot(1)

        # Verify slices
        assert loaded_slot.slice_count == 4
        slices = loaded_slot.get_all_slices_ms(sample_rate=44100)
        assert slices[0] == (0, 250, None)
        assert slices[3] == (750, 1000, None)

    def test_slice_with_loop_roundtrip(self, markers_file, temp_dir):
        """Test that loop points survive write/read cycle."""
        slot = markers_file.get_slot(1)

        # Set slice with loop
        slot.set_slice_ms(0, start_ms=0, end_ms=1000, loop_ms=500, sample_rate=44100)

        # Write slot back to markers file (get_slot returns a copy)
        markers_file.set_slot(1, slot)

        # Write and read
        path = temp_dir / "markers.work"
        markers_file.to_file(path)
        loaded = MarkersFile.from_file(path)

        # Verify
        start, end, loop = loaded.get_slot(1).get_slice_ms(0, sample_rate=44100)
        assert loop == 500
