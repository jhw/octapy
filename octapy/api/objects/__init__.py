"""
Standalone object implementations for octapy.

These objects own their data and can be created with constructor arguments.
They support read/write for serialization and can be used independently
or attached to container objects.
"""

# Phase 1: Leaf objects
from .recorder import RecorderSetup
from .step import AudioStep
from .midi_step import MidiStep

# Phase 2: Track objects
from .audio_part_track import AudioPartTrack
from .audio_pattern_track import AudioPatternTrack
from .midi_part_track import MidiPartTrack
from .midi_pattern_track import MidiPatternTrack

# Phase 3: Container objects
from .scene_track import SceneTrack
from .scene import Scene
from .part import Part
from .pattern import Pattern

__all__ = [
    # Phase 1
    "RecorderSetup",
    "AudioStep",
    "MidiStep",
    # Phase 2
    "AudioPartTrack",
    "AudioPatternTrack",
    "MidiPartTrack",
    "MidiPatternTrack",
    # Phase 3
    "SceneTrack",
    "Scene",
    "Part",
    "Pattern",
]
