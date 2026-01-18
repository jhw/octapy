"""
SamplerPartTrack - base class for sampler machines (Flex/Static).
"""

from __future__ import annotations

from typing import Union

from ..._io import FlexStaticParamsOffset, FlexStaticSetupOffset
from ..enums import LoopMode, SliceMode, LengthMode, RateMode, TimestretchMode
from .audio import AudioPartTrack


class SamplerPartTrack(AudioPartTrack):
    """
    Base class for sampler machines (Flex and Static).

    Provides shared SRC and Setup page parameters. Subclasses override
    _values_offset() and _setup_offset() to point to the correct machine data.

    SRC Page Encoders (Playback):
        A: PTCH (pitch)           - pitch property (0-127, 64 = no transpose)
        B: STRT (start)           - start property (0-127)
        C: LEN (length)           - length property (0-127, 127 = full length)
        D: RATE (rate)            - rate property (0-127, 64 = normal, <64 = reverse)
        E: RTRG (retrig)          - retrig property
        F: RTIM (retrig time)     - retrig_time property

    Setup Page Encoders (FUNC+SRC):
        A: LOOP (loop mode)       - loop_mode property (LoopMode enum)
        B: SLIC (slice mode)      - slice_mode property (SliceMode enum)
        C: LEN (length mode)      - length_mode property (LengthMode enum)
        D: RATE (rate mode)       - rate_mode property (RateMode enum)
        E: TSTR (timestretch)     - timestretch_mode property (TimestretchMode enum)
        F: TSNS (timestretch sens) - timestretch_sensitivity property (0-127)
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

    # === Setup page (FUNC+SRC) ===

    @property
    def loop_mode(self) -> LoopMode:
        """Get/set loop mode (LoopMode enum)."""
        return LoopMode(self._data[self._setup_offset() + FlexStaticSetupOffset.LOOP])

    @loop_mode.setter
    def loop_mode(self, value: Union[LoopMode, int]):
        self._data[self._setup_offset() + FlexStaticSetupOffset.LOOP] = int(value) & 0x7F

    @property
    def slice_mode(self) -> SliceMode:
        """Get/set slice mode (SliceMode enum)."""
        return SliceMode(self._data[self._setup_offset() + FlexStaticSetupOffset.SLIC])

    @slice_mode.setter
    def slice_mode(self, value: Union[SliceMode, int]):
        self._data[self._setup_offset() + FlexStaticSetupOffset.SLIC] = int(value) & 0x7F

    @property
    def length_mode(self) -> LengthMode:
        """
        Get/set length mode (LengthMode enum).

        Controls how the LEN encoder on the main SRC page behaves.
        Set to LengthMode.TIME to enable sample length control.
        """
        return LengthMode(self._data[self._setup_offset() + FlexStaticSetupOffset.LEN])

    @length_mode.setter
    def length_mode(self, value: Union[LengthMode, int]):
        self._data[self._setup_offset() + FlexStaticSetupOffset.LEN] = int(value) & 0x7F

    @property
    def rate_mode(self) -> RateMode:
        """
        Get/set rate mode (RateMode enum).

        Controls whether RATE affects pitch or timestretch.
        Set to RateMode.PITCH to enable reverse playback with negative rate values.
        """
        return RateMode(self._data[self._setup_offset() + FlexStaticSetupOffset.RATE])

    @rate_mode.setter
    def rate_mode(self, value: Union[RateMode, int]):
        self._data[self._setup_offset() + FlexStaticSetupOffset.RATE] = int(value) & 0x7F

    @property
    def timestretch_mode(self) -> TimestretchMode:
        """
        Get/set timestretch mode (TimestretchMode enum).

        Set to TimestretchMode.OFF to disable timestretch and enable reverse playback.
        """
        return TimestretchMode(self._data[self._setup_offset() + FlexStaticSetupOffset.TSTR])

    @timestretch_mode.setter
    def timestretch_mode(self, value: Union[TimestretchMode, int]):
        self._data[self._setup_offset() + FlexStaticSetupOffset.TSTR] = int(value) & 0x7F

    @property
    def timestretch_sensitivity(self) -> int:
        """Get/set timestretch sensitivity (0-127, 64 = default)."""
        return self._data[self._setup_offset() + FlexStaticSetupOffset.TSNS]

    @timestretch_sensitivity.setter
    def timestretch_sensitivity(self, value: int):
        self._data[self._setup_offset() + FlexStaticSetupOffset.TSNS] = value & 0x7F
