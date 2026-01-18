"""
Scene module - scene track locks for crossfader morphing.

Provides typed access to scene parameter locks for audio tracks.
"""

from .base import BaseSceneTrack
from .audio import AudioSceneTrack
from .sampler import SamplerSceneTrack
from .thru import ThruSceneTrack
from .neighbor import NeighborSceneTrack
from .scene import Scene

__all__ = [
    "BaseSceneTrack",
    "AudioSceneTrack",
    "SamplerSceneTrack",
    "ThruSceneTrack",
    "NeighborSceneTrack",
    "Scene",
]
