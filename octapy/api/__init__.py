"""
octapy.api - Octatrack project API.

High-level Pythonic API:
    from octapy import Project, MachineType, TrigCondition
    project = Project.from_template("MY PROJECT")

Low-level file I/O (internal use):
    from octapy._io import BankFile, MarkersFile, ProjectFile
"""

from .enums import (
    MachineType,
    FX1Type,
    FX2Type,
    ScaleMode,
    PatternScale,
    TrigCondition,
    SampleDuration,
    OctapyError,
    SlotLimitExceeded,
    InvalidSlotNumber,
)

from .project import Project
from .bank import Bank
from .part import Part, AudioPartTrack, MidiPartTrack
from .pattern import Pattern, AudioPatternTrack
from .step import AudioStep
from .sample_pool import SamplePool
