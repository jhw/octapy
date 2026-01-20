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

# Standalone objects (Phase 6: complete migration)
from .objects import (
    # Phase 1: Leaf objects
    RecorderSetup,
    AudioStep,
    MidiStep,
    # Phase 2: Track objects
    AudioPartTrack,
    AudioPatternTrack,
    MidiPartTrack,
    MidiPatternTrack,
    # Phase 3: Container objects
    SceneTrack,
    Scene,
    Part,
    Pattern,
    # Phase 4: Top-level objects
    Bank,
    Project,
)

from .settings import Settings, RenderSettings
from .sample_pool import SamplePool

# Backward compatibility aliases
FlexPartTrack = AudioPartTrack
StaticPartTrack = AudioPartTrack
ThruPartTrack = AudioPartTrack
NeighborPartTrack = AudioPartTrack
SamplerStep = AudioStep
