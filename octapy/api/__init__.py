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
    RecordingSource,
    RecTrigMode,
    QRecMode,
)
from .slot_manager import (
    OctapyError,
    SlotLimitExceeded,
    InvalidSlotNumber,
)

# Core objects
from .core import (
    AudioRecorderSetup,
    AudioStep,
    MidiStep,
    AudioPartTrack,
    AudioPatternTrack,
    MidiPartTrack,
    MidiPatternTrack,
    AudioSceneTrack,
    Scene,
    Part,
    Pattern,
    Bank,
    Project,
)

from .settings import Settings, RenderSettings
from .sample_pool import SamplePool
