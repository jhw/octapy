"""
Markers file types and I/O for Octatrack.

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

Ported from ot-tools-io (Rust).
"""

from enum import IntEnum
from pathlib import Path
from typing import List

from . import OTBlock, read_u32_be, write_u32_be, read_u16_be, write_u16_be


# Markers file constants
MARKERS_HEADER = bytes([
    0x46, 0x4f, 0x52, 0x4d, 0x00, 0x00, 0x00, 0x00,
    0x44, 0x50, 0x53, 0x31, 0x53, 0x41, 0x4d, 0x50,
    0x00, 0x00, 0x00, 0x00, 0x00
])  # "FORM....DPS1SAMP....."
MARKERS_FILE_VERSION = 4

# Slot configuration
NUM_FLEX_SLOTS = 136      # 128 sample + 8 recorder
NUM_STATIC_SLOTS = 128
SLOT_SIZE = 0x310         # 784 bytes per slot
NUM_SLICES = 64           # 64 slices per slot


class MarkersOffset(IntEnum):
    """Offsets within the markers file."""
    HEADER = 0                      # 21 bytes
    VERSION = 21                    # 1 byte
    FLEX_SLOTS = 0x1A               # 26 bytes in, flex slots start
    # Static slots follow flex slots: 0x1A + 136 * 0x310 = 0x29CDA
    # Checksum at end: 2 bytes before EOF


class SlotOffset(IntEnum):
    """Offsets within a slot block (784 bytes)."""
    SAMPLE_LENGTH = 0               # 4 bytes (big-endian uint32)
    TRIM_START = 4                  # 4 bytes (big-endian uint32)
    TRIM_END = 8                    # 4 bytes (big-endian uint32)
    LOOP_POINT = 12                 # 4 bytes (big-endian uint32)
    SLICES = 16                     # 64 slices × 12 bytes each


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


class MarkersFile(OTBlock):
    """
    Octatrack markers file containing playback settings for all sample slots.

    Uses pym8-style buffer-based access with typed helpers.
    """

    def __init__(self):
        super().__init__()
        # Calculate file size
        flex_size = NUM_FLEX_SLOTS * SLOT_SIZE
        static_size = NUM_STATIC_SLOTS * SLOT_SIZE
        self._file_size = MarkersOffset.FLEX_SLOTS + flex_size + static_size + 2
        self._data = bytearray(self._file_size)

        # Initialize header and version
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
        """
        Create a new markers file from the embedded template.

        Returns:
            New MarkersFile instance with default values
        """
        from .projects import read_template_file
        data = read_template_file("markers.work")
        return cls.read(data)

    # === Header and version ===

    @property
    def header(self) -> bytes:
        """Get the file header."""
        return bytes(self._data[0:21])

    @property
    def version(self) -> int:
        """Get the file version."""
        return self._data[MarkersOffset.VERSION]

    def check_header(self) -> bool:
        """Verify the header matches expected markers file header."""
        return self.header == MARKERS_HEADER

    def check_version(self) -> bool:
        """Verify the file version is supported."""
        return self.version == MARKERS_FILE_VERSION

    # === Slot access ===

    def _get_slot_offset(self, slot: int, is_static: bool = False) -> int:
        """
        Calculate byte offset for a slot.

        Args:
            slot: Slot number (1-indexed)
            is_static: If True, access static slot instead of flex slot

        Returns:
            Byte offset into the file
        """
        if is_static:
            base = MarkersOffset.FLEX_SLOTS + NUM_FLEX_SLOTS * SLOT_SIZE
            return base + (slot - 1) * SLOT_SIZE
        else:
            return MarkersOffset.FLEX_SLOTS + (slot - 1) * SLOT_SIZE

    def get_slot(self, slot: int, is_static: bool = False) -> SlotMarkers:
        """
        Get a SlotMarkers view for a slot.

        Args:
            slot: Slot number (1-indexed, 1-128 for samples, 129-136 for recorders)
            is_static: If True, get static slot instead of flex slot

        Returns:
            SlotMarkers instance
        """
        offset = self._get_slot_offset(slot, is_static)
        slot_data = self._data[offset:offset + SLOT_SIZE]

        markers = SlotMarkers.__new__(SlotMarkers)
        markers._data = bytearray(slot_data)
        return markers

    def set_slot(self, slot: int, markers: SlotMarkers, is_static: bool = False):
        """
        Write SlotMarkers data back to the file.

        Args:
            slot: Slot number (1-indexed)
            markers: SlotMarkers with data to write
            is_static: If True, write to static slot
        """
        offset = self._get_slot_offset(slot, is_static)
        self._data[offset:offset + SLOT_SIZE] = markers._data

    # === Convenience methods ===

    def get_sample_length(self, slot: int, is_static: bool = False) -> int:
        """
        Get the sample length for a slot.

        Args:
            slot: Slot number (1-indexed)
            is_static: If True, read from static slot

        Returns:
            Sample length in frames
        """
        offset = self._get_slot_offset(slot, is_static)
        return read_u32_be(self._data, offset)

    def set_sample_length(self, slot: int, length: int, is_static: bool = False):
        """
        Set the sample length for a slot.

        Args:
            slot: Slot number (1-indexed)
            length: Sample length in frames
            is_static: If True, write to static slot
        """
        offset = self._get_slot_offset(slot, is_static)
        write_u32_be(self._data, offset, length)

    # === Checksum ===

    def calculate_checksum(self) -> int:
        """
        Calculate checksum for markers file.

        The checksum is sum of bytes from offset 0x14 to end,
        excluding the 2 checksum bytes. Returns 16-bit value.
        """
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

    # === Write helper ===

    def write(self) -> bytes:
        """Get the markers data as bytes (includes checksum update)."""
        self.update_checksum()
        return bytes(self._data)
