"""
octapy.api - Buffer-based binary I/O for Octatrack files.

Follows pym8-style pattern:
- Classes maintain raw _data bytearray
- Offsets defined as IntEnum
- read()/write() methods for serialization
- Properties for typed access
"""

# Re-export from base module
from .base import (
    OTBlock,
    MachineType,
    FX1Type,
    FX2Type,
    ScaleMode,
    PatternScale,
    split_byte,
    join_nibbles,
    _read_fixed_string,
    _write_fixed_string,
    read_u16_le,
    write_u16_le,
    read_u16_be,
    write_u16_be,
    read_u32_be,
    write_u32_be,
)
