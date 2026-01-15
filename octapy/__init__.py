"""
octapy - Python library for Elektron Octatrack binary file I/O.

Ported from ot-tools-io (Rust) by Mike Robeson [dijksterhuis].
Uses pym8-style buffer-based serialization.
"""

# Re-export main API classes
from .api import (
    OTBlock,
    MachineType,
    FX1Type,
    FX2Type,
    ScaleMode,
    PatternScale,
)
from .api.banks import BankFile, BankOffset
from .api.patterns import Pattern, PatternArray, AudioTrack
from .api.parts import Part, Parts, PartOffset
from .api.markers import MarkersFile, SlotMarkers
from .api.projects import (
    ProjectFile,
    SampleSlot,
    zip_project,
    unzip_project,
    extract_template,
    read_template_file,
)

__version__ = "0.1.0"
__all__ = [
    # Core classes
    "BankFile",
    "Pattern",
    "PatternArray",
    "AudioTrack",
    "Part",
    "Parts",
    "MarkersFile",
    "SlotMarkers",
    "ProjectFile",
    "SampleSlot",
    # Project utilities
    "zip_project",
    "unzip_project",
    "extract_template",
    "read_template_file",
    # Base class
    "OTBlock",
    # Enums
    "MachineType",
    "FX1Type",
    "FX2Type",
    "ScaleMode",
    "PatternScale",
    # Offset enums
    "BankOffset",
    "PartOffset",
]
