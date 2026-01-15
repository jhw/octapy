"""
octapy.api - Buffer-based binary I/O for Octatrack files.

Follows pym8-style pattern:
- Classes maintain raw _data bytearray
- Offsets defined as IntEnum
- read()/write() methods for serialization
- Properties for typed access
"""

from enum import IntEnum


def split_byte(byte_value):
    """Split a byte into two nibbles (high 4 bits, low 4 bits)."""
    high_nibble = (byte_value >> 4) & 0x0F
    low_nibble = byte_value & 0x0F
    return high_nibble, low_nibble


def join_nibbles(high_nibble, low_nibble):
    """Join two nibbles into a single byte."""
    return ((high_nibble & 0x0F) << 4) | (low_nibble & 0x0F)


def _read_fixed_string(data, offset, length):
    """Read fixed-length string from binary data, handling null bytes."""
    str_bytes = data[offset:offset + length]

    # Truncate at null byte if present
    null_idx = str_bytes.find(0)
    if null_idx != -1:
        str_bytes = str_bytes[:null_idx]

    return str_bytes.decode('utf-8', errors='replace').strip()


def _write_fixed_string(string, length):
    """Encode string as fixed-length byte array with null byte padding."""
    encoded = string.encode('utf-8')

    if len(encoded) > length:
        encoded = encoded[:length]
    if len(encoded) < length:
        encoded = encoded + bytes([0] * (length - len(encoded)))

    return encoded


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
    """Base class for Octatrack data blocks."""

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

    def get(self, offset):
        """Get byte at offset."""
        return self._data[offset]

    def set(self, offset, value):
        """Set byte at offset."""
        self._data[offset] = value & 0xFF

    def clone(self):
        """Create a copy of this block."""
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance


# Machine types (for audio tracks in Parts)
class MachineType(IntEnum):
    """Machine types for audio tracks."""
    STATIC = 0
    FLEX = 1
    THRU = 2
    NEIGHBOR = 3
    PICKUP = 4


# FX types for audio tracks
class FX1Type(IntEnum):
    """FX1 slot effect types."""
    OFF = 0
    FILTER = 4
    SPATIALIZER = 5
    EQ = 12
    DJ_EQ = 13
    PHASER = 16
    FLANGER = 17
    CHORUS = 18
    COMB_FILTER = 19
    COMPRESSOR = 24
    LOFI = 25


class FX2Type(IntEnum):
    """FX2 slot effect types (includes delay/reverb)."""
    OFF = 0
    FILTER = 4
    SPATIALIZER = 5
    DELAY = 8
    EQ = 12
    DJ_EQ = 13
    PHASER = 16
    FLANGER = 17
    CHORUS = 18
    COMB_FILTER = 19
    PLATE_REVERB = 20
    SPRING_REVERB = 21
    DARK_REVERB = 22
    COMPRESSOR = 24
    LOFI = 25


# Pattern scale modes
class ScaleMode(IntEnum):
    """Pattern scale modes."""
    NORMAL = 0
    PER_TRACK = 1


class PatternScale(IntEnum):
    """Pattern playback speed multipliers."""
    X2 = 0       # 2x speed
    X3_2 = 1     # 3/2x speed
    X1 = 2       # 1x speed (default)
    X3_4 = 3     # 3/4x speed
    X1_2 = 4     # 1/2x speed
    X1_4 = 5     # 1/4x speed
    X1_8 = 6     # 1/8x speed
