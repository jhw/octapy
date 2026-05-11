"""
AudioLfo - per-LFO accessor for AudioPartTrack.

Provides Pythonic access to one of the 3 LFOs on an audio track:
    track.lfo(1).speed = 32
    track.lfo(2).waveform = LfoWaveform.SIN
    track.lfo(3).destination = some_dest_index
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .part_track import AudioPartTrack


# Offsets within the 24-byte AudioTrackParamsValues block for the 3 LFOs.
_LFO_SPD_BASE = 0   # bytes 0, 1, 2 = spd1, spd2, spd3
_LFO_DEP_BASE = 3   # bytes 3, 4, 5 = dep1, dep2, dep3

# Offsets within the 30-byte AudioTrackParamsSetup block for the 3 LFOs.
_LFO_PMTR_BASE = 0   # bytes 0, 1, 2 = lfo1_pmtr, lfo2_pmtr, lfo3_pmtr
_LFO_WAVE_BASE = 3   # bytes 3, 4, 5 = lfo1_wave, lfo2_wave, lfo3_wave
_LFO_MULT_BASE = 24  # bytes 24, 25, 26
_LFO_TRIG_BASE = 27  # bytes 27, 28, 29


class AudioLfo:
    """
    One LFO on an audio track (1 of 3).

    Backed by:
    - Speed/depth bytes in `AudioTrackParamsValues` (LFO_SPDn, LFO_DEPn)
    - Destination/waveform bytes in `AudioTrackParamsSetup` (LFOn_PMTR, LFOn_WAVE)
    - Multiplier/trig bytes in `AudioTrackParamsSetup` (LFOn_MULT, LFOn_TRIG)

    Usage:
        from octapy import LfoWaveform, LfoTrigMode
        track.lfo(1).waveform = LfoWaveform.SIN
        track.lfo(1).speed = 32
        track.lfo(1).depth = 100
        track.lfo(1).destination = 12         # raw destination index
        track.lfo(1).multiplier = 7
        track.lfo(1).trig_mode = LfoTrigMode.TRIG
    """

    __slots__ = ('_track', '_n', '_idx')

    def __init__(self, track: "AudioPartTrack", n: int):
        if not 1 <= n <= 3:
            raise ValueError(f"LFO number must be 1, 2, or 3 — got {n}")
        object.__setattr__(self, '_track', track)
        object.__setattr__(self, '_n', n)
        object.__setattr__(self, '_idx', n - 1)

    def _values(self, base: int) -> int:
        from .part_track import TrackDataOffset
        return TrackDataOffset.TRACK_PARAMS + base + self._idx

    def _setup(self, base: int) -> int:
        from .part_track import TrackDataOffset
        return TrackDataOffset.TRACK_PARAMS_SETUP + base + self._idx

    @property
    def n(self) -> int:
        """LFO number (1, 2, or 3)."""
        return self._n

    # === Values page (FUNC+LFO encoders A and B) ===

    @property
    def speed(self) -> int:
        """LFO speed (0-127)."""
        return self._track._data[self._values(_LFO_SPD_BASE)]

    @speed.setter
    def speed(self, value: int):
        self._track._data[self._values(_LFO_SPD_BASE)] = value & 0x7F

    @property
    def depth(self) -> int:
        """LFO depth (0-127)."""
        return self._track._data[self._values(_LFO_DEP_BASE)]

    @depth.setter
    def depth(self, value: int):
        self._track._data[self._values(_LFO_DEP_BASE)] = value & 0x7F

    # === Setup page (FUNC+LFO encoders C/D/E/F) ===

    @property
    def destination(self) -> int:
        """LFO target parameter (raw index — exact mapping depends on the OS).

        On the Octatrack this corresponds to the DEST setting on the LFO setup page.
        """
        return self._track._data[self._setup(_LFO_PMTR_BASE)]

    @destination.setter
    def destination(self, value: int):
        self._track._data[self._setup(_LFO_PMTR_BASE)] = value & 0xFF

    @property
    def waveform(self) -> int:
        """LFO waveform shape (use the LfoWaveform enum)."""
        return self._track._data[self._setup(_LFO_WAVE_BASE)]

    @waveform.setter
    def waveform(self, value: int):
        self._track._data[self._setup(_LFO_WAVE_BASE)] = int(value) & 0xFF

    @property
    def multiplier(self) -> int:
        """LFO speed multiplier (raw index).

        The Octatrack maps this value to discrete multipliers (1x, 2x, …,
        1/2x, …) via the MULT encoder on the LFO setup page.
        """
        return self._track._data[self._setup(_LFO_MULT_BASE)]

    @multiplier.setter
    def multiplier(self, value: int):
        self._track._data[self._setup(_LFO_MULT_BASE)] = value & 0xFF

    @property
    def trig_mode(self) -> int:
        """LFO trig (retrigger) mode (use the LfoTrigMode enum)."""
        return self._track._data[self._setup(_LFO_TRIG_BASE)]

    @trig_mode.setter
    def trig_mode(self, value: int):
        self._track._data[self._setup(_LFO_TRIG_BASE)] = int(value) & 0xFF

    def __repr__(self) -> str:
        return (
            f"AudioLfo(n={self._n}, speed={self.speed}, depth={self.depth}, "
            f"destination={self.destination}, waveform={self.waveform}, "
            f"multiplier={self.multiplier}, trig_mode={self.trig_mode})"
        )
