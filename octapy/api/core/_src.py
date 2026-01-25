"""
SrcAccessor - dynamic parameter name access for SRC/playback page.

Provides named access to machine parameters based on the current machine type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .audio.part_track import AudioPartTrack
    from .audio.scene_track import AudioSceneTrack

from ..enums import MachineType


# Mapping from machine type to SRC page parameter names (param1-6)
# None means the parameter is unused for that machine type
SRC_PARAM_NAMES: Dict[MachineType, Tuple[Optional[str], ...]] = {
    # Flex/Static (Sampler): pitch, start, length, rate, retrig, retrig_time
    MachineType.FLEX: ('pitch', 'start', 'length', 'rate', 'retrig', 'retrig_time'),
    MachineType.STATIC: ('pitch', 'start', 'length', 'rate', 'retrig', 'retrig_time'),

    # Thru: in_ab, vol_ab, (unused), in_cd, vol_cd, (unused)
    MachineType.THRU: ('in_ab', 'vol_ab', None, 'in_cd', 'vol_cd', None),

    # Neighbor: all unused
    MachineType.NEIGHBOR: (None, None, None, None, None, None),

    # Pickup: pitch, dir, length, (unused), gain, op
    MachineType.PICKUP: ('pitch', 'dir', 'length', None, 'gain', 'op'),
}


class SrcAccessor:
    """
    Provides dynamic named access to SRC/playback page parameters.

    The parameter names change based on the machine type.

    Usage with AudioPartTrack:
        track = AudioPartTrack(machine_type=MachineType.FLEX)
        track.src.pitch = 64     # Same as setting playback param1
        track.src.retrig = 32    # Same as setting playback param5

        track.machine_type = MachineType.THRU
        track.src.in_ab = 1      # Now param1 is 'in_ab'
        track.src.vol_ab = 100   # param2 is 'vol_ab'

    Usage with AudioSceneTrack (requires machine_type):
        scene_track = AudioSceneTrack(track_num=1, machine_type=MachineType.FLEX)
        scene_track.src.pitch = 64  # Lock pitch to 64
    """

    __slots__ = ('_track', '_get_machine_type', '_get_param', '_set_param')

    def __init__(
        self,
        track,
        get_machine_type,
        get_param,
        set_param,
    ):
        """
        Create a SrcAccessor.

        Args:
            track: The track object this accessor is attached to
            get_machine_type: Callable that returns the machine type
            get_param: Callable(n) that gets playback param n (1-6)
            set_param: Callable(n, value) that sets playback param n (1-6)
        """
        object.__setattr__(self, '_track', track)
        object.__setattr__(self, '_get_machine_type', get_machine_type)
        object.__setattr__(self, '_get_param', get_param)
        object.__setattr__(self, '_set_param', set_param)

    def _get_param_names(self) -> Tuple[Optional[str], ...]:
        """Get parameter names for current machine type."""
        machine_type = self._get_machine_type()
        if machine_type is None:
            return (None,) * 6
        return SRC_PARAM_NAMES.get(machine_type, (None,) * 6)

    def _name_to_param_index(self, name: str) -> Optional[int]:
        """Convert parameter name to index (1-6) or None if not found."""
        names = self._get_param_names()
        if name in names:
            return names.index(name) + 1
        return None

    @property
    def machine_type(self):
        """Get the machine type for this accessor."""
        return self._get_machine_type()

    def get_param_names(self) -> List[str]:
        """Get list of valid parameter names for current machine type."""
        return [n for n in self._get_param_names() if n is not None]

    def __getattr__(self, name: str):
        # Handle special cases
        if name.startswith('_') or name == 'machine_type':
            return object.__getattribute__(self, name)

        idx = self._name_to_param_index(name)
        if idx is not None:
            return self._get_param(idx)

        machine_type = self._get_machine_type()
        valid_names = self.get_param_names()
        raise AttributeError(
            f"Machine type {machine_type} has no SRC parameter '{name}'. "
            f"Valid parameters: {valid_names}"
        )

    def __setattr__(self, name: str, value):
        # Handle special cases
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return

        idx = self._name_to_param_index(name)
        if idx is not None:
            self._set_param(idx, value)
            return

        machine_type = self._get_machine_type()
        valid_names = self.get_param_names()
        raise AttributeError(
            f"Machine type {machine_type} has no SRC parameter '{name}'. "
            f"Valid parameters: {valid_names}"
        )

    def __repr__(self) -> str:
        machine_type = self._get_machine_type()
        return f"SrcAccessor(machine_type={machine_type})"
