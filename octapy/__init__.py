"""
octapy - Python library for Elektron Octatrack binary file I/O.

High-level API for creating and manipulating Octatrack projects.

Example:
    from octapy import Project, MachineType, TrigCondition

    # Create a project
    project = Project.from_template("MY PROJECT")

    # Configure a bank
    bank = project.bank(1)

    # Sound configuration via Part -> AudioPartTrack
    part = bank.part(1)
    track = part.track(1)  # Returns AudioPartTrack
    track.machine_type = MachineType.FLEX
    track.flex_slot = 0

    # Sequence programming via Pattern -> AudioPatternTrack -> AudioStep
    pattern = bank.pattern(1)
    pattern.part = 1
    pattern.track(1).active_steps = [1, 5, 9, 13]  # Returns AudioPatternTrack
    pattern.track(1).step(5).condition = TrigCondition.FILL  # Returns AudioStep

    # Add a sample (slot auto-assigned, flex_count auto-updated)
    project.add_sample("../AUDIO/kick.wav")

    # Save
    project.to_zip("output.zip")
"""

# Enums
from .api.enums import (
    MachineType,
    ThruInput,
    FX1Type,
    FX2Type,
    TrigCondition,
    NoteLength,
    # Sampler Setup page (FUNC+SRC)
    LoopMode,
    SliceMode,
    LengthMode,
    RateMode,
    TimestretchMode,
    # Recorder Setup
    RecordingSource,
    RecTrigMode,
    QRecMode,
    ScaleMode,
    PatternScale,
)

# Exceptions
from .api.slot_manager import (
    OctapyError,
    SlotLimitExceeded,
    InvalidSlotNumber,
)

# High-level API classes (from standalone objects)
from .api import (
    # Leaf objects
    AudioRecorderSetup,
    AudioStep,
    MidiStep,
    # Track objects
    AudioPartTrack,
    AudioPatternTrack,
    MidiPartTrack,
    MidiPatternTrack,
    # Container objects
    AudioSceneTrack,
    Scene,
    Part,
    Pattern,
    # Top-level objects
    Bank,
    Project,
    # Settings
    Settings,
    RenderSettings,
    # Utilities
    SamplePool,
    # Backward compatibility aliases
    FlexPartTrack,
    StaticPartTrack,
    ThruPartTrack,
    NeighborPartTrack,
    SamplerStep,
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "Project",
    "Bank",
    "Part",
    "Pattern",
    "Scene",
    "AudioSceneTrack",
    # Track classes
    "AudioPartTrack",
    "AudioPatternTrack",
    "MidiPartTrack",
    "MidiPatternTrack",
    # Step classes
    "AudioStep",
    "MidiStep",
    # Utilities
    "SamplePool",
    "AudioRecorderSetup",
    "Settings",
    "RenderSettings",
    # Backward compatibility aliases
    "FlexPartTrack",
    "StaticPartTrack",
    "ThruPartTrack",
    "NeighborPartTrack",
    "SamplerStep",
    # Enums
    "MachineType",
    "ThruInput",
    "FX1Type",
    "FX2Type",
    "TrigCondition",
    "NoteLength",
    "LoopMode",
    "SliceMode",
    "LengthMode",
    "RateMode",
    "TimestretchMode",
    "RecordingSource",
    "RecTrigMode",
    "QRecMode",
    "ScaleMode",
    "PatternScale",
    # Exceptions
    "OctapyError",
    "SlotLimitExceeded",
    "InvalidSlotNumber",
]
