"""
PickupPartTrack - Pickup machine track configuration.
"""

from __future__ import annotations

from ..._io import MachineParamsOffset, PickupParamsOffset, PickupSetupOffset
from .audio import AudioPartTrack


class PickupPartTrack(AudioPartTrack):
    """
    Pickup machine track configuration.

    Provides access to Pickup-specific parameters for looping/recording.

    SRC Page Encoders:
        A: PTCH (pitch)           - pitch property
        B: DIR (direction)        - direction property
        C: LEN (length)           - length property
        D: (unused)
        E: GAIN (recording gain)  - gain property
        F: OP (operation mode)    - operation property

    Setup Page Encoders:
        A-D: (unused)
        E: TSTR (timestretch)     - timestretch property
        F: TSNS (timestretch sens) - timestretch_sensitivity property

    Usage:
        track = part.pickup_track(1)
        track.pitch = 64      # No transpose
        track.direction = 2   # Playback direction (default)
        track.gain = 64       # Recording gain
        track.operation = 1   # Operation mode
    """

    def _values_offset(self) -> int:
        """Get offset for Pickup params values."""
        return self._machine_params_values_offset(MachineParamsOffset.PICKUP)

    def _setup_offset(self) -> int:
        """Get offset for Pickup params setup."""
        return self._machine_params_setup_offset(MachineParamsOffset.PICKUP)

    # === Playback page (Values) ===

    @property
    def pitch(self) -> int:
        """Get/set pitch (0-127, 64 = no transpose)."""
        return self._data[self._values_offset() + PickupParamsOffset.PTCH]

    @pitch.setter
    def pitch(self, value: int):
        self._data[self._values_offset() + PickupParamsOffset.PTCH] = value & 0x7F

    @property
    def direction(self) -> int:
        """Get/set playback direction (0-127)."""
        return self._data[self._values_offset() + PickupParamsOffset.DIR]

    @direction.setter
    def direction(self, value: int):
        self._data[self._values_offset() + PickupParamsOffset.DIR] = value & 0x7F

    @property
    def length(self) -> int:
        """Get/set loop length (0-127)."""
        return self._data[self._values_offset() + PickupParamsOffset.LEN]

    @length.setter
    def length(self, value: int):
        self._data[self._values_offset() + PickupParamsOffset.LEN] = value & 0x7F

    @property
    def gain(self) -> int:
        """Get/set recording gain (0-127)."""
        return self._data[self._values_offset() + PickupParamsOffset.GAIN]

    @gain.setter
    def gain(self, value: int):
        self._data[self._values_offset() + PickupParamsOffset.GAIN] = value & 0x7F

    @property
    def operation(self) -> int:
        """Get/set operation mode (0-127)."""
        return self._data[self._values_offset() + PickupParamsOffset.OP]

    @operation.setter
    def operation(self, value: int):
        self._data[self._values_offset() + PickupParamsOffset.OP] = value & 0x7F

    # === Setup page ===

    @property
    def timestretch(self) -> int:
        """Get/set timestretch amount (0-127)."""
        return self._data[self._setup_offset() + PickupSetupOffset.TSTR]

    @timestretch.setter
    def timestretch(self, value: int):
        self._data[self._setup_offset() + PickupSetupOffset.TSTR] = value & 0x7F

    @property
    def timestretch_sensitivity(self) -> int:
        """Get/set timestretch sensitivity (0-127)."""
        return self._data[self._setup_offset() + PickupSetupOffset.TSNS]

    @timestretch_sensitivity.setter
    def timestretch_sensitivity(self, value: int):
        self._data[self._setup_offset() + PickupSetupOffset.TSNS] = value & 0x7F
