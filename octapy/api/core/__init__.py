"""
Standalone object implementations for octapy.

These objects own their data and can be created with constructor arguments.
They support read/write for serialization and can be used independently
or attached to container objects.
"""

# Leaf objects
from .recorder import RecorderSetup
from .audio import AudioStep
from .midi import MidiStep

# Track objects
from .audio import AudioPartTrack, AudioPatternTrack
from .midi import MidiPartTrack, MidiPatternTrack

# Container objects
from .scene_track import SceneTrack
from .scene import Scene
from .part import Part
from .pattern import Pattern

# Top-level objects
from .bank import Bank
from .project import Project

__all__ = [
    # Leaf
    "RecorderSetup",
    "AudioStep",
    "MidiStep",
    # Tracks
    "AudioPartTrack",
    "AudioPatternTrack",
    "MidiPartTrack",
    "MidiPatternTrack",
    # Containers
    "SceneTrack",
    "Scene",
    "Part",
    "Pattern",
    # Top-level
    "Bank",
    "Project",
]
