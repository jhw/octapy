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
    OctapyError,
    SlotLimitExceeded,
    InvalidSlotNumber,
)

from .project import Project
from .bank import Bank
from .part import Part, PartTrack
from .pattern import Pattern, PatternTrack
from .step import Step
from .sample_pool import SamplePool
