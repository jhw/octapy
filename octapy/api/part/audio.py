"""
AudioPartTrack - base class for audio track configuration.
"""

from __future__ import annotations

from ..._io import (
    PartOffset,
    MachineSlotOffset,
    AudioTrackParamsOffset,
    MACHINE_SLOT_SIZE,
    MACHINE_PARAMS_SIZE,
    AUDIO_TRACK_PARAMS_SIZE,
)
from ..enums import MachineType
from .base import BasePartTrack


class AudioPartTrack(BasePartTrack):
    """
    Audio track configuration within a Part.

    Provides access to machine type, sample slots, and track settings.
    This is separate from AudioPatternTrack which handles sequencing.

    Usage:
        track = part.track(1)
        track.machine_type = MachineType.FLEX
        track.flex_slot = 0
    """

    @property
    def machine_type(self) -> MachineType:
        """Get/set the machine type for this track."""
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_TYPES + (self._track_num - 1)
        return MachineType(self._data[offset])

    @machine_type.setter
    def machine_type(self, value: MachineType):
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_TYPES + (self._track_num - 1)
        self._data[offset] = int(value)

    def _slot_offset(self) -> int:
        """Get the byte offset for this track's machine slots."""
        return self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE

    @property
    def flex_slot(self) -> int:
        """Get/set the flex sample slot."""
        return self._data[self._slot_offset() + MachineSlotOffset.FLEX_SLOT_ID]

    @flex_slot.setter
    def flex_slot(self, value: int):
        self._data[self._slot_offset() + MachineSlotOffset.FLEX_SLOT_ID] = value & 0xFF

    @property
    def static_slot(self) -> int:
        """Get/set the static sample slot."""
        return self._data[self._slot_offset() + MachineSlotOffset.STATIC_SLOT_ID]

    @static_slot.setter
    def static_slot(self, value: int):
        self._data[self._slot_offset() + MachineSlotOffset.STATIC_SLOT_ID] = value & 0xFF

    @property
    def recorder_slot(self) -> int:
        """Get/set the recorder slot."""
        return self._data[self._slot_offset() + MachineSlotOffset.RECORDER_SLOT_ID]

    @recorder_slot.setter
    def recorder_slot(self, value: int):
        self._data[self._slot_offset() + MachineSlotOffset.RECORDER_SLOT_ID] = value & 0xFF

    @property
    def volume(self) -> tuple:
        """Get the volume as (main, cue) tuple."""
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_VOLUMES + (self._track_num - 1) * 2
        return (self._data[offset], self._data[offset + 1])

    def set_volume(self, main: int = 108, cue: int = 108):
        """Set the volume (main and cue)."""
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_VOLUMES + (self._track_num - 1) * 2
        self._data[offset] = main & 0x7F
        self._data[offset + 1] = cue & 0x7F

    @property
    def fx1_type(self) -> int:
        """Get/set the FX1 type."""
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX1 + (self._track_num - 1)
        return self._data[offset]

    @fx1_type.setter
    def fx1_type(self, value: int):
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX1 + (self._track_num - 1)
        self._data[offset] = value

    @property
    def fx2_type(self) -> int:
        """Get/set the FX2 type."""
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX2 + (self._track_num - 1)
        return self._data[offset]

    @fx2_type.setter
    def fx2_type(self, value: int):
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX2 + (self._track_num - 1)
        self._data[offset] = value

    def _machine_params_values_offset(self, machine_offset: int) -> int:
        """Get offset for machine params values (Playback page)."""
        return (self._part_offset() +
                PartOffset.AUDIO_TRACK_MACHINE_PARAMS_VALUES +
                (self._track_num - 1) * MACHINE_PARAMS_SIZE +
                machine_offset)

    def _machine_params_setup_offset(self, machine_offset: int) -> int:
        """Get offset for machine params setup (Setup page)."""
        return (self._part_offset() +
                PartOffset.AUDIO_TRACK_MACHINE_PARAMS_SETUP +
                (self._track_num - 1) * MACHINE_PARAMS_SIZE +
                machine_offset)

    def _track_params_offset(self) -> int:
        """Get offset for track params (LFO/AMP/FX pages)."""
        return (self._part_offset() +
                PartOffset.AUDIO_TRACK_PARAMS_VALUES +
                (self._track_num - 1) * AUDIO_TRACK_PARAMS_SIZE)

    # === LFO Page (shared across all audio machines) ===
    #
    # LFO Page Encoders:
    #     A: SPD1 (speed 1)   - lfo_speed1 property
    #     B: SPD2 (speed 2)   - lfo_speed2 property
    #     C: SPD3 (speed 3)   - lfo_speed3 property
    #     D: DEP1 (depth 1)   - lfo_depth1 property
    #     E: DEP2 (depth 2)   - lfo_depth2 property
    #     F: DEP3 (depth 3)   - lfo_depth3 property

    @property
    def lfo_speed1(self) -> int:
        """Get/set LFO 1 speed (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_SPD1]

    @lfo_speed1.setter
    def lfo_speed1(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_SPD1] = value & 0x7F

    @property
    def lfo_speed2(self) -> int:
        """Get/set LFO 2 speed (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_SPD2]

    @lfo_speed2.setter
    def lfo_speed2(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_SPD2] = value & 0x7F

    @property
    def lfo_speed3(self) -> int:
        """Get/set LFO 3 speed (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_SPD3]

    @lfo_speed3.setter
    def lfo_speed3(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_SPD3] = value & 0x7F

    @property
    def lfo_depth1(self) -> int:
        """Get/set LFO 1 depth (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_DEP1]

    @lfo_depth1.setter
    def lfo_depth1(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_DEP1] = value & 0x7F

    @property
    def lfo_depth2(self) -> int:
        """Get/set LFO 2 depth (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_DEP2]

    @lfo_depth2.setter
    def lfo_depth2(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_DEP2] = value & 0x7F

    @property
    def lfo_depth3(self) -> int:
        """Get/set LFO 3 depth (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_DEP3]

    @lfo_depth3.setter
    def lfo_depth3(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.LFO_DEP3] = value & 0x7F

    # === AMP Page (shared across all audio machines) ===
    #
    # AMP Page Encoders:
    #     A: ATK (attack)     - attack property
    #     B: HOLD (hold)      - hold property
    #     C: REL (release)    - release property
    #     D: VOL (volume)     - amp_volume property
    #     E: BAL (balance)    - balance property
    #     F: (unused)

    @property
    def attack(self) -> int:
        """Get/set amplitude attack (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_ATK]

    @attack.setter
    def attack(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_ATK] = value & 0x7F

    @property
    def hold(self) -> int:
        """Get/set amplitude hold (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_HOLD]

    @hold.setter
    def hold(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_HOLD] = value & 0x7F

    @property
    def release(self) -> int:
        """Get/set amplitude release (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_REL]

    @release.setter
    def release(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_REL] = value & 0x7F

    @property
    def amp_volume(self) -> int:
        """Get/set amplitude volume (0-127)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_VOL]

    @amp_volume.setter
    def amp_volume(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_VOL] = value & 0x7F

    @property
    def balance(self) -> int:
        """Get/set amplitude balance (0-127, 64 = center)."""
        return self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_BAL]

    @balance.setter
    def balance(self, value: int):
        self._data[self._track_params_offset() + AudioTrackParamsOffset.AMP_BAL] = value & 0x7F
