"""
PageAccessor - generic named parameter accessor for Octatrack pages.

Provides dynamic named access to parameters based on a type-dependent
lookup table. Used for SRC, setup, AMP, and FX pages.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from ..enums import FX1Type, FX2Type, MachineType


# =============================================================================
# Parameter name mappings
# =============================================================================

# SRC playback page: names depend on machine type (6 params)
SRC_PARAM_NAMES: Dict[MachineType, Tuple[Optional[str], ...]] = {
    MachineType.FLEX: ('pitch', 'start', 'length', 'rate', 'retrig', 'retrig_time'),
    MachineType.STATIC: ('pitch', 'start', 'length', 'rate', 'retrig', 'retrig_time'),
    MachineType.THRU: ('in_ab', 'vol_ab', None, 'in_cd', 'vol_cd', None),
    MachineType.NEIGHBOR: (None, None, None, None, None, None),
    MachineType.PICKUP: ('pitch', 'dir', 'length', None, 'gain', 'op'),
}

# SRC setup page: names depend on machine type (6 params)
SRC_SETUP_PARAM_NAMES: Dict[MachineType, Tuple[Optional[str], ...]] = {
    MachineType.FLEX: ('loop', 'slice', 'length_mode', 'rate_mode', 'timestretch', 'timestretch_sensitivity'),
    MachineType.STATIC: ('loop', 'slice', 'length_mode', 'rate_mode', 'timestretch', 'timestretch_sensitivity'),
    MachineType.THRU: (None, None, None, None, None, None),
    MachineType.NEIGHBOR: (None, None, None, None, None, None),
    MachineType.PICKUP: (None, None, None, None, None, None),
}

# AMP page: fixed names, same for all machine types (5 params + 1 unused)
_AMP_KEY = 'AMP'
AMP_PARAM_NAMES: Dict[str, Tuple[Optional[str], ...]] = {
    _AMP_KEY: ('attack', 'hold', 'release', 'volume', 'balance', None),
}

# Value transforms for parameters that need offset adjustment
# Maps param name to (get_transform, set_transform, min_value, max_value)
# get_transform: raw -> display, set_transform: display -> raw
SRC_VALUE_TRANSFORMS: Dict[str, Tuple[Callable, Callable, int, int]] = {
    # retrig: raw 0-127 maps to display 1-128 (number of plays)
    'retrig': (lambda x: x + 1, lambda x: x - 1, 1, 128),
}

# FX pages: names depend on FX type (6 params)
FX_PARAM_NAMES: Dict[int, Tuple[Optional[str], ...]] = {
    FX1Type.OFF: (None, None, None, None, None, None),
    FX1Type.FILTER: ('base', 'width', 'q', 'depth', 'attack', 'decay'),
    FX1Type.SPATIALIZER: ('input', 'depth', 'width', 'high_pass', 'low_pass', 'send'),
    FX2Type.DELAY: ('time', 'feedback', 'volume', 'base', 'width', 'send'),
    FX1Type.EQ: ('freq1', 'gain1', 'q1', 'freq2', 'gain2', 'q2'),
    FX1Type.DJ_EQ: ('ls_f', None, 'rs_f', 'low_gain', 'mid_gain', 'high_gain'),
    FX1Type.PHASER: ('center', 'depth', 'spread', 'feedback', 'width', 'mix'),
    FX1Type.FLANGER: ('delay', 'depth', 'spread', 'feedback', 'width', 'mix'),
    FX1Type.CHORUS: ('delay', 'depth', 'spread', 'feedback', 'width', 'mix'),
    FX1Type.COMB_FILTER: ('pitch', 'tune', 'low_pass', 'feedback', None, 'mix'),
    FX2Type.PLATE_REVERB: ('time', 'damp', 'gate', 'high_pass', 'low_pass', 'mix'),
    FX2Type.SPRING_REVERB: ('time', None, None, 'high_pass', 'low_pass', 'mix'),
    FX2Type.DARK_REVERB: ('time', 'shug', 'shuf', 'high_pass', 'low_pass', 'mix'),
    FX1Type.COMPRESSOR: ('attack', 'release', 'threshold', 'ratio', 'gain', 'mix'),
    FX1Type.LOFI: ('dist', None, 'amf', 'srr', 'brr', 'amd'),
}


# =============================================================================
# PageAccessor
# =============================================================================

class PageAccessor:
    """
    Generic named parameter accessor for Octatrack pages.

    Maps parameter names to indices (1-6) based on a type-dependent lookup
    table. Works for SRC, setup, AMP, and FX pages.

    Usage:
        track.src.pitch = 64         # SRC playback (machine-type-dependent)
        track.src.retrig = 2         # Play sample twice (1-indexed)
        track.setup.loop = 0         # SRC setup (machine-type-dependent)
        track.amp.attack = 10        # AMP page (fixed names)
        track.fx1.base = 100         # FX1 (FX-type-dependent)
    """

    __slots__ = ('_page_name', '_param_names_map', '_get_type', '_get_param', '_set_param', '_value_transforms')

    def __init__(
        self,
        page_name: str,
        param_names_map: Dict,
        get_type: Callable,
        get_param: Callable[[int], Optional[int]],
        set_param: Callable[[int, int], None],
        value_transforms: Optional[Dict[str, Tuple[Callable, Callable, int, int]]] = None,
    ):
        """
        Create a PageAccessor.

        Args:
            page_name: Page name for error messages ("SRC", "setup", "AMP", "FX1")
            param_names_map: Dict mapping type keys to tuples of param names
            get_type: Callable returning the current type key for name lookup
            get_param: Callable(n) that gets param n (1-6)
            set_param: Callable(n, value) that sets param n (1-6)
            value_transforms: Optional dict mapping param names to
                (get_transform, set_transform, min_value, max_value) tuples
        """
        object.__setattr__(self, '_page_name', page_name)
        object.__setattr__(self, '_param_names_map', param_names_map)
        object.__setattr__(self, '_get_type', get_type)
        object.__setattr__(self, '_get_param', get_param)
        object.__setattr__(self, '_set_param', set_param)
        object.__setattr__(self, '_value_transforms', value_transforms or {})

    def _get_param_names(self) -> Tuple[Optional[str], ...]:
        """Get parameter names for current type."""
        type_key = self._get_type()
        if type_key is None:
            return (None,) * 6
        return self._param_names_map.get(type_key, (None,) * 6)

    def _name_to_param_index(self, name: str) -> Optional[int]:
        """Convert parameter name to index (1-6) or None if not found."""
        names = self._get_param_names()
        if name in names:
            return names.index(name) + 1
        return None

    def get_param_names(self) -> List[str]:
        """Get list of valid parameter names for current type."""
        return [n for n in self._get_param_names() if n is not None]

    def __getattr__(self, name: str):
        if name.startswith('_'):
            return object.__getattribute__(self, name)

        idx = self._name_to_param_index(name)
        if idx is not None:
            raw_value = self._get_param(idx)
            # Apply get transform if defined
            if name in self._value_transforms:
                get_transform, _, _, _ = self._value_transforms[name]
                return get_transform(raw_value)
            return raw_value

        valid_names = self.get_param_names()
        raise AttributeError(
            f"{self._page_name} page has no parameter '{name}'. "
            f"Valid parameters: {valid_names}"
        )

    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return

        idx = self._name_to_param_index(name)
        if idx is not None:
            # Apply set transform and validation if defined
            if name in self._value_transforms:
                _, set_transform, min_val, max_val = self._value_transforms[name]
                if not min_val <= value <= max_val:
                    raise ValueError(f"{name} must be {min_val}-{max_val}, got {value}")
                value = set_transform(value)
            self._set_param(idx, value)
            return

        valid_names = self.get_param_names()
        raise AttributeError(
            f"{self._page_name} page has no parameter '{name}'. "
            f"Valid parameters: {valid_names}"
        )

    def __repr__(self) -> str:
        return f"PageAccessor({self._page_name})"
