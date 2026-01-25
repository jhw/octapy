"""
FXAccessor - dynamic parameter name access for FX slots.

Provides named access to FX parameters based on the current FX type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from .audio.part_track import AudioPartTrack
    from .audio.scene_track import AudioSceneTrack

from ..enums import FX1Type, FX2Type


# Mapping from FX type values to parameter names (param1-6)
# None means the parameter is unused for that FX type
FX_PARAM_NAMES: Dict[int, Tuple[Optional[str], ...]] = {
    # OFF has no meaningful params
    FX1Type.OFF: (None, None, None, None, None, None),

    # FILTER: base, width, q, depth, attack, decay
    FX1Type.FILTER: ('base', 'width', 'q', 'depth', 'attack', 'decay'),

    # SPATIALIZER: input, depth, width, high_pass, low_pass, send
    FX1Type.SPATIALIZER: ('input', 'depth', 'width', 'high_pass', 'low_pass', 'send'),

    # DELAY (FX2 only): time, feedback, volume, base, width, send
    FX2Type.DELAY: ('time', 'feedback', 'volume', 'base', 'width', 'send'),

    # EQ: freq1, gain1, q1, freq2, gain2, q2
    FX1Type.EQ: ('freq1', 'gain1', 'q1', 'freq2', 'gain2', 'q2'),

    # DJ_EQ: ls_f, (unused), rs_f, low_gain, mid_gain, high_gain
    FX1Type.DJ_EQ: ('ls_f', None, 'rs_f', 'low_gain', 'mid_gain', 'high_gain'),

    # PHASER: center, depth, spread, feedback, width, mix
    FX1Type.PHASER: ('center', 'depth', 'spread', 'feedback', 'width', 'mix'),

    # FLANGER: delay, depth, spread, feedback, width, mix
    FX1Type.FLANGER: ('delay', 'depth', 'spread', 'feedback', 'width', 'mix'),

    # CHORUS: delay, depth, spread, feedback, width, mix
    FX1Type.CHORUS: ('delay', 'depth', 'spread', 'feedback', 'width', 'mix'),

    # COMB_FILTER: pitch, tune, low_pass, feedback, (unused), mix
    FX1Type.COMB_FILTER: ('pitch', 'tune', 'low_pass', 'feedback', None, 'mix'),

    # PLATE_REVERB (FX2 only): time, damp, gate, high_pass, low_pass, mix
    FX2Type.PLATE_REVERB: ('time', 'damp', 'gate', 'high_pass', 'low_pass', 'mix'),

    # SPRING_REVERB (FX2 only): time, (unused), (unused), high_pass, low_pass, mix
    FX2Type.SPRING_REVERB: ('time', None, None, 'high_pass', 'low_pass', 'mix'),

    # DARK_REVERB (FX2 only): time, shug, shuf, high_pass, low_pass, mix
    FX2Type.DARK_REVERB: ('time', 'shug', 'shuf', 'high_pass', 'low_pass', 'mix'),

    # COMPRESSOR: attack, release, threshold, ratio, gain, mix
    FX1Type.COMPRESSOR: ('attack', 'release', 'threshold', 'ratio', 'gain', 'mix'),

    # LOFI: dist, (unused), amf, srr, brr, amd
    FX1Type.LOFI: ('dist', None, 'amf', 'srr', 'brr', 'amd'),
}


class FXAccessor:
    """
    Provides dynamic named access to FX parameters.

    The parameter names change based on the current FX type.

    Usage with AudioPartTrack:
        track = AudioPartTrack(fx1_type=FX1Type.FILTER)
        track.fx1.base = 64      # Same as track.fx1_param1 = 64
        track.fx1.mix = 100      # Same as track.fx1_param6 = 100

        # Change FX type and names change too
        track.fx1_type = FX1Type.CHORUS
        track.fx1.delay = 64     # Now param1 is 'delay'

    Usage with AudioSceneTrack (requires fx_type):
        scene_track = AudioSceneTrack(track_num=1, fx1_type=FX1Type.FILTER)
        scene_track.fx1.base = 64  # Lock filter base to 64
    """

    __slots__ = ('_track', '_slot', '_get_type', '_set_type', '_get_param', '_set_param')

    def __init__(
        self,
        track: Union["AudioPartTrack", "AudioSceneTrack"],
        slot: int,
        get_type: Callable[[], Optional[int]],
        set_type: Optional[Callable[[int], None]],
        get_param: Callable[[int], Optional[int]],
        set_param: Callable[[int, Optional[int]], None],
    ):
        """
        Create an FXAccessor.

        Args:
            track: The track object this accessor is attached to
            slot: FX slot number (1 or 2)
            get_type: Callable that returns the FX type
            set_type: Callable that sets the FX type (or None if read-only)
            get_param: Callable(n) that gets FX param n (1-6)
            set_param: Callable(n, value) that sets FX param n (1-6)
        """
        object.__setattr__(self, '_track', track)
        object.__setattr__(self, '_slot', slot)
        object.__setattr__(self, '_get_type', get_type)
        object.__setattr__(self, '_set_type', set_type)
        object.__setattr__(self, '_get_param', get_param)
        object.__setattr__(self, '_set_param', set_param)

    def _get_param_names(self) -> Tuple[Optional[str], ...]:
        """Get parameter names for current FX type."""
        fx_type = self._get_type()
        if fx_type is None:
            return (None,) * 6
        return FX_PARAM_NAMES.get(fx_type, (None,) * 6)

    def _name_to_param_index(self, name: str) -> Optional[int]:
        """Convert parameter name to index (1-6) or None if not found."""
        names = self._get_param_names()
        if name in names:
            return names.index(name) + 1
        return None

    @property
    def type(self) -> Optional[int]:
        """Get/set the FX type for this slot."""
        return self._get_type()

    @type.setter
    def type(self, value: int):
        if self._set_type is None:
            raise AttributeError("FX type is read-only for this track")
        self._set_type(value)

    def get_param_names(self) -> List[str]:
        """Get list of valid parameter names for current FX type."""
        return [n for n in self._get_param_names() if n is not None]

    def __getattr__(self, name: str):
        # Handle special cases
        if name.startswith('_') or name == 'type':
            return object.__getattribute__(self, name)

        idx = self._name_to_param_index(name)
        if idx is not None:
            return self._get_param(idx)

        fx_type = self._get_type()
        valid_names = self.get_param_names()
        raise AttributeError(
            f"FX type {fx_type} has no parameter '{name}'. "
            f"Valid parameters: {valid_names}"
        )

    def __setattr__(self, name: str, value):
        # Handle special cases
        if name.startswith('_') or name == 'type':
            object.__setattr__(self, name, value)
            return

        idx = self._name_to_param_index(name)
        if idx is not None:
            self._set_param(idx, value)
            return

        fx_type = self._get_type()
        valid_names = self.get_param_names()
        raise AttributeError(
            f"FX type {fx_type} has no parameter '{name}'. "
            f"Valid parameters: {valid_names}"
        )

    def __repr__(self) -> str:
        fx_type = self._get_type()
        return f"FXAccessor(slot={self._slot}, type={fx_type})"
