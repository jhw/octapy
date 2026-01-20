"""
Standalone object implementations for octapy.

These objects own their data and can be created with constructor arguments.
They support read/write for serialization and can be used independently
or attached to container objects.
"""

from .recorder import RecorderSetup
from .step import AudioStep
from .midi_step import MidiStep

__all__ = [
    "RecorderSetup",
    "AudioStep",
    "MidiStep",
]
