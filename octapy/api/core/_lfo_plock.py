"""
LfoPlock — per-step p-lock accessor for one LFO.

Returned by `audio_step.lfo(n)` and `midi_step.lfo(n)`. Each step has 3 LFOs
and each LFO has two p-lockable values (speed and depth). `LfoPlock` bundles
those into a single accessor with `.speed` and `.depth` properties so the
shape mirrors `track.lfo(n)` from `audio/lfo.py` / `midi/lfo.py`.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .audio.step import AudioStep
    from .midi.step import MidiStep


class LfoPlock:
    """
    P-lock view of one LFO on one step.

    `value` semantics match the rest of the p-lock API: reading returns
    `None` when no lock is set (the step uses the Part default); writing
    `None` clears the lock.

    Usage:
        step.lfo(1).speed = 64        # p-lock LFO 1 speed
        step.lfo(2).depth = 100       # p-lock LFO 2 depth
        step.lfo(1).speed = None      # clear the speed lock
        assert step.lfo(3).speed is None
    """

    __slots__ = ('_step', '_n', '_idx', '_speed_offset', '_depth_offset')

    def __init__(self, step, n: int, speed_offset: int, depth_offset: int):
        if not 1 <= n <= 3:
            raise ValueError(f"LFO number must be 1, 2, or 3 — got {n}")
        object.__setattr__(self, '_step', step)
        object.__setattr__(self, '_n', n)
        object.__setattr__(self, '_idx', n - 1)
        object.__setattr__(self, '_speed_offset', speed_offset + (n - 1))
        object.__setattr__(self, '_depth_offset', depth_offset + (n - 1))

    @property
    def n(self) -> int:
        """LFO number (1, 2, or 3)."""
        return self._n

    @property
    def speed(self) -> Optional[int]:
        """P-locked LFO speed (0-127), or None if no lock is set."""
        return self._step._get_plock(self._speed_offset)

    @speed.setter
    def speed(self, value: Optional[int]):
        self._step._set_plock(self._speed_offset, value)

    @property
    def depth(self) -> Optional[int]:
        """P-locked LFO depth (0-127), or None if no lock is set."""
        return self._step._get_plock(self._depth_offset)

    @depth.setter
    def depth(self, value: Optional[int]):
        self._step._set_plock(self._depth_offset, value)

    def __repr__(self) -> str:
        return f"LfoPlock(n={self._n}, speed={self.speed}, depth={self.depth})"
