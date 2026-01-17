"""
SamplerPartTrack - base class for sampler machines (Flex/Static).
"""

from __future__ import annotations

from ..._io import FlexStaticParamsOffset, FlexStaticSetupOffset
from .audio import AudioPartTrack


class SamplerPartTrack(AudioPartTrack):
    """
    Base class for sampler machines (Flex and Static).

    Provides shared SRC and Setup page parameters. Subclasses override
    _values_offset() and _setup_offset() to point to the correct machine data.

    SRC Page Encoders (Playback):
        A: PTCH (pitch)           - pitch property
        B: STRT (start)           - start property
        C: LEN (length)           - length property
        D: RATE (rate)            - rate property
        E: RTRG (retrig)          - retrig property
        F: RTIM (retrig time)     - retrig_time property

    Setup Page Encoders:
        A: LOOP (loop mode)       - loop property
        B: SLIC (slice mode)      - slice property
        C: LEN (length mode)      - length_mode property
        D: RATE (rate mode)       - rate_mode property
        E: TSTR (timestretch)     - timestretch property
        F: TSNS (timestretch sens) - timestretch_sensitivity property
    """

    def _values_offset(self) -> int:
        """Get offset for machine params values. Override in subclass."""
        raise NotImplementedError

    def _setup_offset(self) -> int:
        """Get offset for machine params setup. Override in subclass."""
        raise NotImplementedError

    # === SRC Page (Playback/Values) ===

    @property
    def pitch(self) -> int:
        """Get/set pitch (0-127, 64 = no transpose)."""
        return self._data[self._values_offset() + FlexStaticParamsOffset.PTCH]

    @pitch.setter
    def pitch(self, value: int):
        self._data[self._values_offset() + FlexStaticParamsOffset.PTCH] = value & 0x7F

    @property
    def start(self) -> int:
        """Get/set sample start point (0-127)."""
        return self._data[self._values_offset() + FlexStaticParamsOffset.STRT]

    @start.setter
    def start(self, value: int):
        self._data[self._values_offset() + FlexStaticParamsOffset.STRT] = value & 0x7F

    @property
    def length(self) -> int:
        """Get/set sample length (0-127)."""
        return self._data[self._values_offset() + FlexStaticParamsOffset.LEN]

    @length.setter
    def length(self, value: int):
        self._data[self._values_offset() + FlexStaticParamsOffset.LEN] = value & 0x7F

    @property
    def rate(self) -> int:
        """Get/set playback rate (0-127)."""
        return self._data[self._values_offset() + FlexStaticParamsOffset.RATE]

    @rate.setter
    def rate(self, value: int):
        self._data[self._values_offset() + FlexStaticParamsOffset.RATE] = value & 0x7F

    @property
    def retrig(self) -> int:
        """Get/set retrig count (0-127)."""
        return self._data[self._values_offset() + FlexStaticParamsOffset.RTRG]

    @retrig.setter
    def retrig(self, value: int):
        self._data[self._values_offset() + FlexStaticParamsOffset.RTRG] = value & 0x7F

    @property
    def retrig_time(self) -> int:
        """Get/set retrig time (0-127)."""
        return self._data[self._values_offset() + FlexStaticParamsOffset.RTIM]

    @retrig_time.setter
    def retrig_time(self, value: int):
        self._data[self._values_offset() + FlexStaticParamsOffset.RTIM] = value & 0x7F

    # === Setup page ===

    @property
    def loop(self) -> int:
        """Get/set loop mode (0-127)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.LOOP]

    @loop.setter
    def loop(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.LOOP] = value & 0x7F

    @property
    def slice(self) -> int:
        """Get/set slice mode (0-127)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.SLIC]

    @slice.setter
    def slice(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.SLIC] = value & 0x7F

    @property
    def length_mode(self) -> int:
        """Get/set length mode (0-127)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.LEN]

    @length_mode.setter
    def length_mode(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.LEN] = value & 0x7F

    @property
    def rate_mode(self) -> int:
        """Get/set rate mode (0-127)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.RATE]

    @rate_mode.setter
    def rate_mode(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.RATE] = value & 0x7F

    @property
    def timestretch(self) -> int:
        """Get/set timestretch amount (0-127)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.TSTR]

    @timestretch.setter
    def timestretch(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.TSTR] = value & 0x7F

    @property
    def timestretch_sensitivity(self) -> int:
        """Get/set timestretch sensitivity (0-127)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.TSNS]

    @timestretch_sensitivity.setter
    def timestretch_sensitivity(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.TSNS] = value & 0x7F
