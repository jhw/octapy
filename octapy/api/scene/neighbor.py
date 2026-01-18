"""
NeighborSceneTrack - scene track for Neighbor machines.
"""

from __future__ import annotations

from .audio import AudioSceneTrack


class NeighborSceneTrack(AudioSceneTrack):
    """
    Scene track for Neighbor machines.

    Neighbor machines have no machine-specific playback parameters.
    Inherits AMP, FX1, FX2 locks from AudioSceneTrack.

    Usage:
        scene = part.scene(1)
        track = scene.neighbor_track(1)

        # AMP/FX locks only (no playback params)
        track.amp_volume = 100
        track.fx1_param1 = 64
    """
    pass
