"""
MidiLfo - per-LFO accessor for MidiPartTrack.

MIDI tracks share the same 3-LFO structure as audio tracks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .part_track import MidiPartTrack


# Offsets within MidiPartTrack._data for the 3 LFOs.
# All offsets are in the contiguous standalone buffer (see TrackDataOffset).
_LFO_SPD_BASE = 6    # bytes 6, 7, 8
_LFO_DEP_BASE = 9    # bytes 9, 10, 11
_LFO_PMTR_BASE = 38  # bytes 38, 39, 40
_LFO_WAVE_BASE = 41  # bytes 41, 42, 43
_LFO_MULT_BASE = 62  # bytes 62, 63, 64
_LFO_TRIG_BASE = 65  # bytes 65, 66, 67


class MidiLfo:
    """
    One LFO on a MIDI track (1 of 3).

    Exposes `speed`, `depth`, `destination`, `waveform`, `multiplier`,
    `trig_mode`. Same shape as `AudioLfo`.

    Usage:
        from octapy import LfoWaveform, LfoTrigMode
        midi_track.lfo(1).waveform = LfoWaveform.TRI
        midi_track.lfo(1).speed = 32
        midi_track.lfo(1).trig_mode = LfoTrigMode.HOLD
    """

    __slots__ = ('_track', '_n', '_idx')

    def __init__(self, track: "MidiPartTrack", n: int):
        if not 1 <= n <= 3:
            raise ValueError(f"LFO number must be 1, 2, or 3 — got {n}")
        object.__setattr__(self, '_track', track)
        object.__setattr__(self, '_n', n)
        object.__setattr__(self, '_idx', n - 1)

    @property
    def n(self) -> int:
        """LFO number (1, 2, or 3)."""
        return self._n

    @property
    def speed(self) -> int:
        """LFO speed (0-127)."""
        return self._track._data[_LFO_SPD_BASE + self._idx]

    @speed.setter
    def speed(self, value: int):
        self._track._data[_LFO_SPD_BASE + self._idx] = value & 0x7F

    @property
    def depth(self) -> int:
        """LFO depth (0-127)."""
        return self._track._data[_LFO_DEP_BASE + self._idx]

    @depth.setter
    def depth(self, value: int):
        self._track._data[_LFO_DEP_BASE + self._idx] = value & 0x7F

    @property
    def destination(self) -> int:
        """LFO target parameter (raw index)."""
        return self._track._data[_LFO_PMTR_BASE + self._idx]

    @destination.setter
    def destination(self, value: int):
        self._track._data[_LFO_PMTR_BASE + self._idx] = value & 0xFF

    @property
    def waveform(self) -> int:
        """LFO waveform shape (use the LfoWaveform enum)."""
        return self._track._data[_LFO_WAVE_BASE + self._idx]

    @waveform.setter
    def waveform(self, value: int):
        self._track._data[_LFO_WAVE_BASE + self._idx] = int(value) & 0xFF

    @property
    def multiplier(self) -> int:
        """LFO speed multiplier (raw index)."""
        return self._track._data[_LFO_MULT_BASE + self._idx]

    @multiplier.setter
    def multiplier(self, value: int):
        self._track._data[_LFO_MULT_BASE + self._idx] = value & 0xFF

    @property
    def trig_mode(self) -> int:
        """LFO trig (retrigger) mode (use the LfoTrigMode enum)."""
        return self._track._data[_LFO_TRIG_BASE + self._idx]

    @trig_mode.setter
    def trig_mode(self, value: int):
        self._track._data[_LFO_TRIG_BASE + self._idx] = int(value) & 0xFF

    def __repr__(self) -> str:
        return (
            f"MidiLfo(n={self._n}, speed={self.speed}, depth={self.depth}, "
            f"destination={self.destination}, waveform={self.waveform}, "
            f"multiplier={self.multiplier}, trig_mode={self.trig_mode})"
        )
