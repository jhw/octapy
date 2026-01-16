"""
Low-level binary I/O utilities for Octatrack files.

Follows pym8-style pattern:
- Classes maintain raw _data bytearray
- Offsets defined as IntEnum
- read()/write() methods for serialization
"""


def read_u16_le(data, offset):
    """Read little-endian uint16."""
    return data[offset] | (data[offset + 1] << 8)


def write_u16_le(data, offset, value):
    """Write little-endian uint16."""
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF


def read_u16_be(data, offset):
    """Read big-endian uint16."""
    return (data[offset] << 8) | data[offset + 1]


def write_u16_be(data, offset, value):
    """Write big-endian uint16."""
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


def read_u32_be(data, offset):
    """Read big-endian uint32."""
    return (
        (data[offset] << 24) |
        (data[offset + 1] << 16) |
        (data[offset + 2] << 8) |
        data[offset + 3]
    )


def write_u32_be(data, offset, value):
    """Write big-endian uint32."""
    data[offset] = (value >> 24) & 0xFF
    data[offset + 1] = (value >> 16) & 0xFF
    data[offset + 2] = (value >> 8) & 0xFF
    data[offset + 3] = value & 0xFF


class OTBlock:
    """Base class for Octatrack binary data blocks."""

    BLOCK_SIZE = 0  # Subclasses should override

    def __init__(self):
        self._data = bytearray()

    @classmethod
    def read(cls, data):
        """Read block from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BLOCK_SIZE] if cls.BLOCK_SIZE else data)
        return instance

    def write(self):
        """Write block to binary data."""
        return bytes(self._data)

    def clone(self):
        """Create a copy of this block."""
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance
