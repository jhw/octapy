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
    ThruInput,
    FX1Type,
    FX2Type,
    ScaleMode,
    PatternScale,
    TrigCondition,
    NoteLength,
)
from .slot_manager import (
    OctapyError,
    SlotLimitExceeded,
    InvalidSlotNumber,
)

from .project import Project
from .bank import Bank
from .part import (
    Part,
    AudioPartTrack,
    FlexPartTrack,
    StaticPartTrack,
    ThruPartTrack,
    NeighborPartTrack,
    PickupPartTrack,
    MidiPartTrack,
)
from .pattern import Pattern, AudioPatternTrack, MidiPatternTrack
from .step import AudioStep, MidiStep
from .sample_pool import SamplePool
