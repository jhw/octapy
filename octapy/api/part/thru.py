"""
ThruPartTrack - Thru machine track configuration.
"""

from __future__ import annotations

from ..._io import MachineParamsOffset, ThruParamsOffset
from ..enums import ThruInput
from .audio import AudioPartTrack


class ThruPartTrack(AudioPartTrack):
    """
    Thru machine track configuration.

    Provides access to Thru-specific parameters for live audio input routing.

    SRC Page Encoders:
        A: IN AB (input select)   - in_ab property (ThruInput enum)
        B: VOL (volume A/B)       - vol_ab property
        C: (unused)
        D: IN CD (input select)   - in_cd property (ThruInput enum)
        E: VOL (volume C/D)       - vol_cd property
        F: (unused)

    Input Selection (ThruInput enum):
        OFF = 0      - Input disabled
        A_PLUS_B = 1 - A+B combined (stereo pair)
        A = 2        - Input A only (left)
        B = 3        - Input B only (right)
        A_B = 4      - A/B (both separate)

    Usage:
        from octapy import ThruInput
        track = part.thru_track(1)
        track.in_ab = ThruInput.A_PLUS_B  # Route stereo input
        track.vol_ab = 100                 # Set volume
    """

    def _values_offset(self) -> int:
        """Get offset for Thru params values."""
        return self._machine_params_values_offset(MachineParamsOffset.THRU)

    # === SRC Page (Values) ===

    @property
    def in_ab(self) -> ThruInput:
        """Get/set input A/B selection. See ThruInput enum."""
        return ThruInput(self._data[self._values_offset() + ThruParamsOffset.IN_AB])

    @in_ab.setter
    def in_ab(self, value: int):
        self._data[self._values_offset() + ThruParamsOffset.IN_AB] = int(value) & 0x7F

    @property
    def vol_ab(self) -> int:
        """Get/set volume A/B (0-127)."""
        return self._data[self._values_offset() + ThruParamsOffset.VOL_AB]

    @vol_ab.setter
    def vol_ab(self, value: int):
        self._data[self._values_offset() + ThruParamsOffset.VOL_AB] = value & 0x7F

    @property
    def in_cd(self) -> ThruInput:
        """Get/set input C/D selection. See ThruInput enum."""
        return ThruInput(self._data[self._values_offset() + ThruParamsOffset.IN_CD])

    @in_cd.setter
    def in_cd(self, value: int):
        self._data[self._values_offset() + ThruParamsOffset.IN_CD] = int(value) & 0x7F

    @property
    def vol_cd(self) -> int:
        """Get/set volume C/D (0-127)."""
        return self._data[self._values_offset() + ThruParamsOffset.VOL_CD]

    @vol_cd.setter
    def vol_cd(self, value: int):
        self._data[self._values_offset() + ThruParamsOffset.VOL_CD] = value & 0x7F

    def to_dict(self) -> dict:
        """
        Convert Thru part track to dictionary.

        Extends AudioPartTrack to_dict with Thru-specific input routing.
        """
        result = super().to_dict()
        result["src"] = {
            "in_ab": self.in_ab.name,
            "vol_ab": self.vol_ab,
            "in_cd": self.in_cd.name,
            "vol_cd": self.vol_cd,
        }
        return result
