"""
NeighborPartTrack - Neighbor machine track configuration.
"""

from __future__ import annotations

from .audio import AudioPartTrack


class NeighborPartTrack(AudioPartTrack):
    """
    Neighbor machine track configuration.

    Neighbor machines route audio from adjacent tracks.
    The SRC page has no active encoders - all parameters are unused.

    SRC Page Encoders:
        A-F: (all unused)

    Usage:
        track = part.neighbor_track(1)
        # No machine-specific params - just uses base AudioPartTrack features
        # (machine_type, volume, fx1_type, fx2_type, etc.)
    """
    pass
