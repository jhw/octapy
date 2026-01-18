"""
FX module - effect containers for FX1 and FX2 slots.

Provides typed access to effect-specific parameters based on the FX type.
"""

from typing import TYPE_CHECKING, Union

from ..enums import FX1Type, FX2Type

from .base import BaseFX, OffFX
from .filter import FilterFX
from .spatial import SpatializerFX
from .delay import DelayFX
from .eq import EqFX, DjEqFX
from .modulation import PhaserFX, FlangerFX, ChorusFX, CombFilterFX
from .reverb import PlateReverbFX, SpringReverbFX, DarkReverbFX
from .dynamics import CompressorFX
from .lofi import LofiFX

if TYPE_CHECKING:
    from ..part.audio import AudioPartTrack


# Map FX type enum values to their container classes
_FX_CLASS_MAP = {
    0: OffFX,           # OFF
    4: FilterFX,        # FILTER
    5: SpatializerFX,   # SPATIALIZER
    8: DelayFX,         # DELAY (FX2 only)
    12: EqFX,           # EQ
    13: DjEqFX,         # DJ_EQ
    16: PhaserFX,       # PHASER
    17: FlangerFX,      # FLANGER
    18: ChorusFX,       # CHORUS
    19: CombFilterFX,   # COMB_FILTER
    20: PlateReverbFX,  # PLATE_REVERB (FX2 only)
    21: SpringReverbFX, # SPRING_REVERB (FX2 only)
    22: DarkReverbFX,   # DARK_REVERB (FX2 only)
    24: CompressorFX,   # COMPRESSOR
    25: LofiFX,         # LOFI
}


def create_fx(part_track: "AudioPartTrack", slot: int, fx_type: int) -> BaseFX:
    """
    Create an FX container for the given type.

    Args:
        part_track: The AudioPartTrack this FX belongs to
        slot: 1 for FX1, 2 for FX2
        fx_type: FX type enum value

    Returns:
        FX container instance with type-specific properties
    """
    cls = _FX_CLASS_MAP.get(fx_type, OffFX)
    return cls(part_track, slot)


__all__ = [
    # Base
    "BaseFX",
    "OffFX",
    # FX types
    "FilterFX",
    "SpatializerFX",
    "DelayFX",
    "EqFX",
    "DjEqFX",
    "PhaserFX",
    "FlangerFX",
    "ChorusFX",
    "CombFilterFX",
    "PlateReverbFX",
    "SpringReverbFX",
    "DarkReverbFX",
    "CompressorFX",
    "LofiFX",
    # Factory
    "create_fx",
]
