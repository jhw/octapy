"""
Markers file I/O for Octatrack.

The markers file (markers.work) contains playback settings for loaded sample slots:
- Sample length (frame count)
- Trim start/end points
- Loop point
- Slices (up to 64 per slot)

There are 136 flex slots (128 sample + 8 recorder) and 128 static slots.

File layout:
- Header: 21 bytes ("FORM....DPS1SAMP.....")
- Version: 1 byte (4)
- Flex slots: 136 × 784 bytes
- Static slots: 128 × 784 bytes
- Checksum: 2 bytes (big-endian)

Slice data format (per slice, 12 bytes):
- trim_start: 4 bytes (big-endian uint32) - start position in audio samples
- trim_end: 4 bytes (big-endian uint32) - end position in audio samples
- loop_start: 4 bytes (big-endian uint32) - loop point (0xFFFFFFFF = disabled)
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import List, Optional, Tuple

from .base import OTBlock, read_u32_be, write_u32_be, read_u16_be, write_u16_be


# =============================================================================
# Constants
# =============================================================================

MARKERS_HEADER = bytes([
    0x46, 0x4f, 0x52, 0x4d, 0x00, 0x00, 0x00, 0x00,
    0x44, 0x50, 0x53, 0x31, 0x53, 0x41, 0x4d, 0x50,
    0x00, 0x00, 0x00, 0x00, 0x00
])  # "FORM....DPS1SAMP....."
MARKERS_FILE_VERSION = 4

NUM_FLEX_SLOTS = 136      # 128 sample + 8 recorder
NUM_STATIC_SLOTS = 128
SLOT_SIZE = 0x310         # 784 bytes per slot
NUM_SLICES = 64           # 64 slices per slot
SLICE_SIZE = 12           # 12 bytes per slice (3 × uint32)
SLICE_LOOP_DISABLED = 0xFFFFFFFF  # Magic value for disabled loop point


# =============================================================================
# Slice Data Structure
# =============================================================================

@dataclass
class Slice:
    """
    Slice data for a sample.

    Positions are in audio samples (frames), not milliseconds.
    Use SlotMarkers.get_slice_ms() for millisecond values.

    Attributes:
        trim_start: Start position in audio samples
        trim_end: End position in audio samples
        loop_start: Loop point in audio samples, or None if disabled
    """
    trim_start: int
    trim_end: int
    loop_start: Optional[int] = None  # None = disabled (0xFFFFFFFF)

    def __post_init__(self):
        """Validate slice data."""
        if self.trim_start < 0:
            raise ValueError(f"trim_start must be >= 0, got {self.trim_start}")
        if self.trim_end < self.trim_start:
            raise ValueError(
                f"trim_end ({self.trim_end}) must be >= trim_start ({self.trim_start})"
            )
        if self.loop_start is not None:
            if self.loop_start < self.trim_start:
                raise ValueError(
                    f"loop_start ({self.loop_start}) must be >= trim_start ({self.trim_start})"
                )
            if self.loop_start >= self.trim_end:
                raise ValueError(
                    f"loop_start ({self.loop_start}) must be < trim_end ({self.trim_end})"
                )

    @property
    def is_empty(self) -> bool:
        """Check if this slice is empty (start == end == 0)."""
        return self.trim_start == 0 and self.trim_end == 0

    def to_raw(self) -> Tuple[int, int, int]:
        """Convert to raw values for storage."""
        loop = SLICE_LOOP_DISABLED if self.loop_start is None else self.loop_start
        return (self.trim_start, self.trim_end, loop)

    @classmethod
    def from_raw(cls, trim_start: int, trim_end: int, loop_start: int) -> "Slice":
        """
        Create from raw storage values.

        Handles special cases:
        - SLICE_LOOP_DISABLED (0xFFFFFFFF) -> loop_start=None
        - Empty slice (start=end=0) with loop=0 -> loop_start=None
        """
        # Treat 0xFFFFFFFF as disabled
        if loop_start == SLICE_LOOP_DISABLED:
            loop = None
        # Treat loop=0 on empty slices as disabled (template default)
        elif trim_start == 0 and trim_end == 0 and loop_start == 0:
            loop = None
        else:
            loop = loop_start
        return cls(trim_start=trim_start, trim_end=trim_end, loop_start=loop)


# =============================================================================
# Offset Enums
# =============================================================================

class MarkersOffset(IntEnum):
    """Offsets within the markers file."""
    HEADER = 0                      # 21 bytes
    VERSION = 21                    # 1 byte
    FLEX_SLOTS = 0x1A               # 26 bytes in, flex slots start


class SlotOffset(IntEnum):
    """Offsets within a slot block (784 bytes)."""
    SAMPLE_LENGTH = 0               # 4 bytes (big-endian uint32)
    TRIM_START = 4                  # 4 bytes (big-endian uint32)
    TRIM_END = 8                    # 4 bytes (big-endian uint32)
    LOOP_POINT = 12                 # 4 bytes (big-endian uint32)
    SLICES = 16                     # 64 slices × 12 bytes each


# =============================================================================
# SlotMarkers Class
# =============================================================================

class SlotMarkers(OTBlock):
    """
    Playback markers for a single sample slot.

    Contains sample length, trim points, loop point, and up to 64 slices.
    """

    BLOCK_SIZE = SLOT_SIZE

    def __init__(self):
        super().__init__()
        self._data = bytearray(SLOT_SIZE)

    @property
    def sample_length(self) -> int:
        """Get the sample length in frames (big-endian uint32)."""
        return read_u32_be(self._data, SlotOffset.SAMPLE_LENGTH)

    @sample_length.setter
    def sample_length(self, value: int):
        """Set the sample length in frames."""
        write_u32_be(self._data, SlotOffset.SAMPLE_LENGTH, value)

    @property
    def trim_start(self) -> int:
        """Get the trim start point in frames."""
        return read_u32_be(self._data, SlotOffset.TRIM_START)

    @trim_start.setter
    def trim_start(self, value: int):
        """Set the trim start point."""
        write_u32_be(self._data, SlotOffset.TRIM_START, value)

    @property
    def trim_end(self) -> int:
        """Get the trim end point in frames."""
        return read_u32_be(self._data, SlotOffset.TRIM_END)

    @trim_end.setter
    def trim_end(self, value: int):
        """Set the trim end point."""
        write_u32_be(self._data, SlotOffset.TRIM_END, value)

    @property
    def loop_point(self) -> int:
        """Get the loop point in frames (0 = disabled for empty slots)."""
        return read_u32_be(self._data, SlotOffset.LOOP_POINT)

    @loop_point.setter
    def loop_point(self, value: int):
        """Set the loop point."""
        write_u32_be(self._data, SlotOffset.LOOP_POINT, value)

    # === Slice access (raw samples) ===

    def _slice_offset(self, index: int) -> int:
        """Get byte offset for a slice by index (0-63)."""
        if not 0 <= index < NUM_SLICES:
            raise IndexError(f"Slice index must be 0-63, got {index}")
        return SlotOffset.SLICES + index * SLICE_SIZE

    def get_slice(self, index: int) -> Slice:
        """
        Get slice by index (0-63) in raw audio samples.

        Args:
            index: Slice index (0-63)

        Returns:
            Slice with trim_start, trim_end, loop_start in audio samples.
            loop_start is None if disabled.
        """
        offset = self._slice_offset(index)
        trim_start = read_u32_be(self._data, offset)
        trim_end = read_u32_be(self._data, offset + 4)
        loop_start = read_u32_be(self._data, offset + 8)
        return Slice.from_raw(trim_start, trim_end, loop_start)

    def set_slice(
        self,
        index: int,
        trim_start: int,
        trim_end: int,
        loop_start: Optional[int] = None,
    ) -> None:
        """
        Set slice by index (0-63) in raw audio samples.

        Args:
            index: Slice index (0-63)
            trim_start: Start position in audio samples
            trim_end: End position in audio samples
            loop_start: Loop point in audio samples, or None to disable
        """
        # Validate by creating a Slice (raises on invalid values)
        slice_obj = Slice(trim_start=trim_start, trim_end=trim_end, loop_start=loop_start)
        start, end, loop = slice_obj.to_raw()

        offset = self._slice_offset(index)
        write_u32_be(self._data, offset, start)
        write_u32_be(self._data, offset + 4, end)
        write_u32_be(self._data, offset + 8, loop)

    def clear_slice(self, index: int) -> None:
        """
        Clear a slice (set to zeros).

        Args:
            index: Slice index (0-63)
        """
        offset = self._slice_offset(index)
        write_u32_be(self._data, offset, 0)
        write_u32_be(self._data, offset + 4, 0)
        write_u32_be(self._data, offset + 8, 0)

    def clear_all_slices(self) -> None:
        """Clear all 64 slices."""
        for i in range(NUM_SLICES):
            self.clear_slice(i)

    @property
    def slice_count(self) -> int:
        """
        Get the number of non-empty slices.

        Returns:
            Count of slices where trim_start != trim_end or either is non-zero.
        """
        count = 0
        for i in range(NUM_SLICES):
            slice_obj = self.get_slice(i)
            if not slice_obj.is_empty:
                count += 1
        return count

    def get_all_slices(self) -> List[Slice]:
        """
        Get all non-empty slices.

        Returns:
            List of Slice objects (only non-empty ones).
        """
        slices = []
        for i in range(NUM_SLICES):
            slice_obj = self.get_slice(i)
            if not slice_obj.is_empty:
                slices.append(slice_obj)
        return slices

    # === Slice access (milliseconds) ===

    @staticmethod
    def _samples_to_ms(samples: int, sample_rate: int) -> int:
        """Convert audio samples to milliseconds."""
        return samples * 1000 // sample_rate

    @staticmethod
    def _ms_to_samples(ms: int, sample_rate: int) -> int:
        """Convert milliseconds to audio samples."""
        return ms * sample_rate // 1000

    def get_slice_ms(
        self,
        index: int,
        sample_rate: int = 44100,
    ) -> Tuple[int, int, Optional[int]]:
        """
        Get slice by index in milliseconds.

        Args:
            index: Slice index (0-63)
            sample_rate: Audio sample rate (default 44100 Hz)

        Returns:
            Tuple of (start_ms, end_ms, loop_ms).
            loop_ms is None if disabled.
        """
        slice_obj = self.get_slice(index)
        start_ms = self._samples_to_ms(slice_obj.trim_start, sample_rate)
        end_ms = self._samples_to_ms(slice_obj.trim_end, sample_rate)
        loop_ms = None
        if slice_obj.loop_start is not None:
            loop_ms = self._samples_to_ms(slice_obj.loop_start, sample_rate)
        return (start_ms, end_ms, loop_ms)

    def set_slice_ms(
        self,
        index: int,
        start_ms: int,
        end_ms: int,
        loop_ms: Optional[int] = None,
        sample_rate: int = 44100,
    ) -> None:
        """
        Set slice by index in milliseconds.

        Args:
            index: Slice index (0-63)
            start_ms: Start position in milliseconds
            end_ms: End position in milliseconds
            loop_ms: Loop point in milliseconds, or None to disable
            sample_rate: Audio sample rate (default 44100 Hz)
        """
        trim_start = self._ms_to_samples(start_ms, sample_rate)
        trim_end = self._ms_to_samples(end_ms, sample_rate)
        loop_start = None
        if loop_ms is not None:
            loop_start = self._ms_to_samples(loop_ms, sample_rate)
        self.set_slice(index, trim_start, trim_end, loop_start)

    def set_slices_ms(
        self,
        slices: List[Tuple[int, int]],
        sample_rate: int = 44100,
    ) -> None:
        """
        Bulk set slices from a list of (start_ms, end_ms) tuples.

        Clears all existing slices first, then sets the provided slices.
        This is the most common workflow for creating slice grids.

        Args:
            slices: List of (start_ms, end_ms) tuples. Max 64 slices.
            sample_rate: Audio sample rate (default 44100 Hz)

        Raises:
            ValueError: If more than 64 slices provided.

        Example:
            # Create 4 equal slices for a 1-second sample
            markers.set_slices_ms([
                (0, 250),
                (250, 500),
                (500, 750),
                (750, 1000),
            ], sample_rate=44100)
        """
        if len(slices) > NUM_SLICES:
            raise ValueError(f"Maximum {NUM_SLICES} slices allowed, got {len(slices)}")

        # Clear all existing slices
        self.clear_all_slices()

        # Set new slices
        for i, (start_ms, end_ms) in enumerate(slices):
            self.set_slice_ms(i, start_ms, end_ms, sample_rate=sample_rate)

    def get_all_slices_ms(
        self,
        sample_rate: int = 44100,
    ) -> List[Tuple[int, int, Optional[int]]]:
        """
        Get all non-empty slices in milliseconds.

        Args:
            sample_rate: Audio sample rate (default 44100 Hz)

        Returns:
            List of (start_ms, end_ms, loop_ms) tuples for non-empty slices.
        """
        result = []
        for i in range(NUM_SLICES):
            slice_obj = self.get_slice(i)
            if not slice_obj.is_empty:
                start_ms = self._samples_to_ms(slice_obj.trim_start, sample_rate)
                end_ms = self._samples_to_ms(slice_obj.trim_end, sample_rate)
                loop_ms = None
                if slice_obj.loop_start is not None:
                    loop_ms = self._samples_to_ms(slice_obj.loop_start, sample_rate)
                result.append((start_ms, end_ms, loop_ms))
        return result


# =============================================================================
# MarkersFile Class
# =============================================================================

class MarkersFile(OTBlock):
    """
    Low-level Octatrack markers file I/O.

    Contains playback settings for all sample slots.
    """

    def __init__(self):
        super().__init__()
        flex_size = NUM_FLEX_SLOTS * SLOT_SIZE
        static_size = NUM_STATIC_SLOTS * SLOT_SIZE
        self._file_size = MarkersOffset.FLEX_SLOTS + flex_size + static_size + 2
        self._data = bytearray(self._file_size)

        self._data[0:21] = MARKERS_HEADER
        self._data[MarkersOffset.VERSION] = MARKERS_FILE_VERSION

    @classmethod
    def read(cls, data) -> "MarkersFile":
        """Read markers from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data)
        instance._file_size = len(data)
        return instance

    @classmethod
    def from_file(cls, path: Path) -> "MarkersFile":
        """Load a markers file from disk."""
        with open(path, 'rb') as f:
            data = f.read()
        return cls.read(data)

    def to_file(self, path: Path):
        """Write the markers file to disk."""
        self.update_checksum()
        with open(path, 'wb') as f:
            f.write(self._data)

    @classmethod
    def new(cls) -> "MarkersFile":
        """Create a new markers file from the embedded template."""
        from .project import read_template_file
        data = read_template_file("markers.work")
        return cls.read(data)

    # === Header and version ===

    @property
    def header(self) -> bytes:
        return bytes(self._data[0:21])

    @property
    def version(self) -> int:
        return self._data[MarkersOffset.VERSION]

    def check_header(self) -> bool:
        return self.header == MARKERS_HEADER

    def check_version(self) -> bool:
        return self.version == MARKERS_FILE_VERSION

    # === Slot access ===

    def _get_slot_offset(self, slot: int, is_static: bool = False) -> int:
        """Calculate byte offset for a slot."""
        if is_static:
            base = MarkersOffset.FLEX_SLOTS + NUM_FLEX_SLOTS * SLOT_SIZE
            return base + (slot - 1) * SLOT_SIZE
        else:
            return MarkersOffset.FLEX_SLOTS + (slot - 1) * SLOT_SIZE

    def get_slot(self, slot: int, is_static: bool = False) -> SlotMarkers:
        """Get a SlotMarkers view for a slot."""
        offset = self._get_slot_offset(slot, is_static)
        slot_data = self._data[offset:offset + SLOT_SIZE]

        markers = SlotMarkers.__new__(SlotMarkers)
        markers._data = bytearray(slot_data)
        return markers

    def set_slot(self, slot: int, markers: SlotMarkers, is_static: bool = False):
        """Write SlotMarkers data back to the file."""
        offset = self._get_slot_offset(slot, is_static)
        self._data[offset:offset + SLOT_SIZE] = markers._data

    # === Convenience methods ===

    def get_sample_length(self, slot: int, is_static: bool = False) -> int:
        """Get the sample length for a slot."""
        offset = self._get_slot_offset(slot, is_static)
        return read_u32_be(self._data, offset)

    def set_sample_length(self, slot: int, length: int, is_static: bool = False):
        """Set the sample length for a slot."""
        offset = self._get_slot_offset(slot, is_static)
        write_u32_be(self._data, offset, length)

    # === Checksum ===

    def calculate_checksum(self) -> int:
        """Calculate checksum for markers file."""
        CHECKSUM_START = 0x14
        total = sum(self._data[CHECKSUM_START:-2])
        return total & 0xFFFF

    def update_checksum(self):
        """Recalculate and update the checksum (big-endian)."""
        checksum = self.calculate_checksum()
        write_u16_be(self._data, len(self._data) - 2, checksum)

    def verify_checksum(self) -> bool:
        """Verify the checksum matches the calculated value."""
        stored = read_u16_be(self._data, len(self._data) - 2)
        return stored == self.calculate_checksum()
