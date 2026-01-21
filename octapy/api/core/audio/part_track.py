"""
AudioPartTrack - standalone audio track configuration for a Part.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Part binary data.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional, TYPE_CHECKING

from ...._io import (
    MachineSlotOffset,
    MachineParamsOffset,
    FlexStaticParamsOffset,
    FlexStaticSetupOffset,
    AudioTrackParamsOffset,
    MACHINE_SLOT_SIZE,
    MACHINE_PARAMS_SIZE,
    AUDIO_TRACK_PARAMS_SIZE,
    RECORDER_SETUP_SIZE,
    FX_DEFAULTS,
    OCTAPY_DEFAULT_SRC_VALUES,
    OCTAPY_DEFAULT_SRC_SETUP,
    TEMPLATE_DEFAULT_AMP,
    TEMPLATE_DEFAULT_FX1_PARAMS,
    TEMPLATE_DEFAULT_FX2_PARAMS,
    TEMPLATE_DEFAULT_FX1_TYPE,
    TEMPLATE_DEFAULT_FX2_TYPE,
)
from ...enums import MachineType, FX1Type, FX2Type
from ..recorder import RecorderSetup


class TrackDataOffset(IntEnum):
    """Offsets within standalone AudioPartTrack buffer.

    This is a contiguous layout for standalone storage:
    - 1 byte: machine_type
    - 1 byte: fx1_type
    - 1 byte: fx2_type
    - 2 bytes: volume (main, cue)
    - 5 bytes: machine_slots
    - 30 bytes: machine_params_values (playback page)
    - 30 bytes: machine_params_setup (setup page)
    - 24 bytes: track_params (LFO/AMP/FX)
    - 12 bytes: recorder_setup
    = 106 bytes total
    """
    MACHINE_TYPE = 0
    FX1_TYPE = 1
    FX2_TYPE = 2
    VOLUME_MAIN = 3
    VOLUME_CUE = 4
    MACHINE_SLOTS = 5          # 5 bytes
    MACHINE_PARAMS_VALUES = 10  # 30 bytes
    MACHINE_PARAMS_SETUP = 40   # 30 bytes
    TRACK_PARAMS = 70           # 24 bytes
    RECORDER_SETUP = 94         # 12 bytes


# Total size of standalone track buffer
AUDIO_PART_TRACK_SIZE = 106


class AudioPartTrack:
    """
    Audio track configuration within a Part.

    This is a standalone object that can be created with constructor arguments
    or read from Part binary data. It owns its data buffer.

    Provides access to machine type, sample slots, volume, AMP settings,
    FX settings, and recorder configuration.

    Usage:
        # Create with constructor arguments
        track = AudioPartTrack(
            track_num=1,
            machine_type=MachineType.FLEX,
            flex_slot=0,
            fx1_type=FX1Type.DJ_EQ,
        )

        # Read from Part binary (called by Part)
        track = AudioPartTrack.read_from_part(track_num, part_data, part_offset)

        # Write to Part binary
        track.write_to_part(part_data, part_offset)
    """

    def __init__(
        self,
        track_num: int = 1,
        machine_type: MachineType = MachineType.FLEX,
        flex_slot: int = 0,
        static_slot: int = 0,
        recorder_slot: int = 0,
        main_volume: int = 108,
        cue_volume: int = 108,
        fx1_type: Optional[int] = None,
        fx2_type: Optional[int] = None,
        # AMP page
        attack: int = 0,
        hold: int = 127,
        release: int = 24,
        amp_volume: int = 108,
        balance: int = 64,
        # Recorder (can pass RecorderSetup or individual args)
        recorder: Optional[RecorderSetup] = None,
    ):
        """
        Create an AudioPartTrack with optional parameter overrides.

        Args:
            track_num: Track number (1-8)
            machine_type: Machine type (FLEX, STATIC, THRU, NEIGHBOR, PICKUP)
            flex_slot: Flex sample slot (0-127)
            static_slot: Static sample slot (0-127)
            recorder_slot: Recorder buffer slot (0-7 for buffers, 128+ for flex slots)
            main_volume: Main output volume (0-127)
            cue_volume: Cue output volume (0-127)
            fx1_type: FX1 effect type
            fx2_type: FX2 effect type
            attack: AMP attack (0-127)
            hold: AMP hold (0-127)
            release: AMP release (0-127)
            amp_volume: AMP volume (0-127)
            balance: AMP balance (0-127, 64=center)
            recorder: RecorderSetup object (or created with defaults)
        """
        self._track_num = track_num
        self._data = bytearray(AUDIO_PART_TRACK_SIZE)

        # Apply defaults
        self._apply_defaults()

        # Apply constructor arguments
        self.machine_type = machine_type
        self.flex_slot = flex_slot
        self.static_slot = static_slot
        self.recorder_slot = recorder_slot
        self.set_volume(main_volume, cue_volume)

        if fx1_type is not None:
            self.fx1_type = fx1_type
        if fx2_type is not None:
            self.fx2_type = fx2_type

        self.attack = attack
        self.hold = hold
        self.release = release
        self.amp_volume = amp_volume
        self.balance = balance

        # Set recorder
        if recorder is not None:
            self._recorder = recorder
        else:
            self._recorder = RecorderSetup()

    def _apply_defaults(self):
        """Apply octapy default values to the buffer."""
        # Machine type defaults to FLEX (but will be overwritten by constructor)
        self._data[TrackDataOffset.MACHINE_TYPE] = int(MachineType.FLEX)

        # FX types
        self._data[TrackDataOffset.FX1_TYPE] = TEMPLATE_DEFAULT_FX1_TYPE
        self._data[TrackDataOffset.FX2_TYPE] = TEMPLATE_DEFAULT_FX2_TYPE

        # Volume
        self._data[TrackDataOffset.VOLUME_MAIN] = 108
        self._data[TrackDataOffset.VOLUME_CUE] = 108

        # Machine slots (all 0)
        for i in range(MACHINE_SLOT_SIZE):
            self._data[TrackDataOffset.MACHINE_SLOTS + i] = 0

        # Machine params values - apply octapy SRC defaults for FLEX
        offset = TrackDataOffset.MACHINE_PARAMS_VALUES + MachineParamsOffset.FLEX
        self._data[offset:offset + 6] = OCTAPY_DEFAULT_SRC_VALUES

        # Machine params setup - apply octapy SRC defaults for FLEX
        offset = TrackDataOffset.MACHINE_PARAMS_SETUP + MachineParamsOffset.FLEX
        self._data[offset:offset + 6] = OCTAPY_DEFAULT_SRC_SETUP

        # Track params - AMP defaults
        offset = TrackDataOffset.TRACK_PARAMS
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_AMP

        # FX1 params
        offset = TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM1
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_FX1_PARAMS

        # FX2 params
        offset = TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM1
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_FX2_PARAMS

        # Recorder setup will be handled by RecorderSetup object

    @classmethod
    def read_from_part(
        cls,
        track_num: int,
        part_data: bytes,
        part_offset: int = 0,
    ) -> "AudioPartTrack":
        """
        Read an AudioPartTrack from Part binary data.

        Extracts track-specific data from the scattered Part layout
        into a standalone object.

        Args:
            track_num: Track number (1-8)
            part_data: Part binary data (or full bank data)
            part_offset: Offset to Part in the data

        Returns:
            AudioPartTrack instance
        """
        from ...._io import PartOffset

        instance = cls.__new__(cls)
        instance._track_num = track_num
        instance._data = bytearray(AUDIO_PART_TRACK_SIZE)

        track_idx = track_num - 1

        # Read machine type
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_TYPES + track_idx
        instance._data[TrackDataOffset.MACHINE_TYPE] = part_data[offset]

        # Read FX types
        offset = part_offset + PartOffset.AUDIO_TRACK_FX1 + track_idx
        instance._data[TrackDataOffset.FX1_TYPE] = part_data[offset]

        offset = part_offset + PartOffset.AUDIO_TRACK_FX2 + track_idx
        instance._data[TrackDataOffset.FX2_TYPE] = part_data[offset]

        # Read volumes
        offset = part_offset + PartOffset.AUDIO_TRACK_VOLUMES + track_idx * 2
        instance._data[TrackDataOffset.VOLUME_MAIN] = part_data[offset]
        instance._data[TrackDataOffset.VOLUME_CUE] = part_data[offset + 1]

        # Read machine slots
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + track_idx * MACHINE_SLOT_SIZE
        instance._data[TrackDataOffset.MACHINE_SLOTS:TrackDataOffset.MACHINE_SLOTS + MACHINE_SLOT_SIZE] = \
            part_data[offset:offset + MACHINE_SLOT_SIZE]

        # Read machine params values
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_PARAMS_VALUES + track_idx * MACHINE_PARAMS_SIZE
        instance._data[TrackDataOffset.MACHINE_PARAMS_VALUES:TrackDataOffset.MACHINE_PARAMS_VALUES + MACHINE_PARAMS_SIZE] = \
            part_data[offset:offset + MACHINE_PARAMS_SIZE]

        # Read machine params setup
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_PARAMS_SETUP + track_idx * MACHINE_PARAMS_SIZE
        instance._data[TrackDataOffset.MACHINE_PARAMS_SETUP:TrackDataOffset.MACHINE_PARAMS_SETUP + MACHINE_PARAMS_SIZE] = \
            part_data[offset:offset + MACHINE_PARAMS_SIZE]

        # Read track params
        offset = part_offset + PartOffset.AUDIO_TRACK_PARAMS_VALUES + track_idx * AUDIO_TRACK_PARAMS_SIZE
        instance._data[TrackDataOffset.TRACK_PARAMS:TrackDataOffset.TRACK_PARAMS + AUDIO_TRACK_PARAMS_SIZE] = \
            part_data[offset:offset + AUDIO_TRACK_PARAMS_SIZE]

        # Read recorder setup into RecorderSetup object
        offset = part_offset + PartOffset.RECORDER_SETUP + track_idx * RECORDER_SETUP_SIZE
        instance._recorder = RecorderSetup.read(part_data[offset:offset + RECORDER_SETUP_SIZE])

        return instance

    def write_to_part(self, part_data: bytearray, part_offset: int = 0):
        """
        Write this AudioPartTrack to Part binary data.

        Scatters track-specific data to the appropriate Part layout locations.

        Args:
            part_data: Part binary data (mutable bytearray)
            part_offset: Offset to Part in the data
        """
        from ...._io import PartOffset

        track_idx = self._track_num - 1

        # Write machine type
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_TYPES + track_idx
        part_data[offset] = self._data[TrackDataOffset.MACHINE_TYPE]

        # Write FX types
        offset = part_offset + PartOffset.AUDIO_TRACK_FX1 + track_idx
        part_data[offset] = self._data[TrackDataOffset.FX1_TYPE]

        offset = part_offset + PartOffset.AUDIO_TRACK_FX2 + track_idx
        part_data[offset] = self._data[TrackDataOffset.FX2_TYPE]

        # Write volumes
        offset = part_offset + PartOffset.AUDIO_TRACK_VOLUMES + track_idx * 2
        part_data[offset] = self._data[TrackDataOffset.VOLUME_MAIN]
        part_data[offset + 1] = self._data[TrackDataOffset.VOLUME_CUE]

        # Write machine slots
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + track_idx * MACHINE_SLOT_SIZE
        part_data[offset:offset + MACHINE_SLOT_SIZE] = \
            self._data[TrackDataOffset.MACHINE_SLOTS:TrackDataOffset.MACHINE_SLOTS + MACHINE_SLOT_SIZE]

        # Write machine params values
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_PARAMS_VALUES + track_idx * MACHINE_PARAMS_SIZE
        part_data[offset:offset + MACHINE_PARAMS_SIZE] = \
            self._data[TrackDataOffset.MACHINE_PARAMS_VALUES:TrackDataOffset.MACHINE_PARAMS_VALUES + MACHINE_PARAMS_SIZE]

        # Write machine params setup
        offset = part_offset + PartOffset.AUDIO_TRACK_MACHINE_PARAMS_SETUP + track_idx * MACHINE_PARAMS_SIZE
        part_data[offset:offset + MACHINE_PARAMS_SIZE] = \
            self._data[TrackDataOffset.MACHINE_PARAMS_SETUP:TrackDataOffset.MACHINE_PARAMS_SETUP + MACHINE_PARAMS_SIZE]

        # Write track params
        offset = part_offset + PartOffset.AUDIO_TRACK_PARAMS_VALUES + track_idx * AUDIO_TRACK_PARAMS_SIZE
        part_data[offset:offset + AUDIO_TRACK_PARAMS_SIZE] = \
            self._data[TrackDataOffset.TRACK_PARAMS:TrackDataOffset.TRACK_PARAMS + AUDIO_TRACK_PARAMS_SIZE]

        # Write recorder setup
        offset = part_offset + PartOffset.RECORDER_SETUP + track_idx * RECORDER_SETUP_SIZE
        part_data[offset:offset + RECORDER_SETUP_SIZE] = self._recorder.write()

    def clone(self) -> "AudioPartTrack":
        """Create a copy of this AudioPartTrack."""
        instance = AudioPartTrack.__new__(AudioPartTrack)
        instance._track_num = self._track_num
        instance._data = bytearray(self._data)
        instance._recorder = self._recorder.clone()
        return instance

    # === Basic properties ===

    @property
    def track_num(self) -> int:
        """Get the track number (1-8)."""
        return self._track_num

    @property
    def machine_type(self) -> MachineType:
        """Get/set the machine type for this track."""
        return MachineType(self._data[TrackDataOffset.MACHINE_TYPE])

    @machine_type.setter
    def machine_type(self, value: MachineType):
        self._data[TrackDataOffset.MACHINE_TYPE] = int(value)

    # === Machine slots ===

    @property
    def flex_slot(self) -> int:
        """Get/set the flex sample slot."""
        return self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.FLEX_SLOT_ID]

    @flex_slot.setter
    def flex_slot(self, value: int):
        self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.FLEX_SLOT_ID] = value & 0xFF

    @property
    def static_slot(self) -> int:
        """Get/set the static sample slot."""
        return self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.STATIC_SLOT_ID]

    @static_slot.setter
    def static_slot(self, value: int):
        self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.STATIC_SLOT_ID] = value & 0xFF

    @property
    def recorder_slot(self) -> int:
        """Get/set the recorder slot."""
        return self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.RECORDER_SLOT_ID]

    @recorder_slot.setter
    def recorder_slot(self, value: int):
        self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.RECORDER_SLOT_ID] = value & 0xFF

    # === Volume ===

    @property
    def volume(self) -> tuple:
        """Get the volume as (main, cue) tuple."""
        return (
            self._data[TrackDataOffset.VOLUME_MAIN],
            self._data[TrackDataOffset.VOLUME_CUE],
        )

    def set_volume(self, main: int = 108, cue: int = 108):
        """Set the volume (main and cue)."""
        self._data[TrackDataOffset.VOLUME_MAIN] = main & 0x7F
        self._data[TrackDataOffset.VOLUME_CUE] = cue & 0x7F

    # === FX types ===

    @property
    def fx1_type(self) -> int:
        """Get/set the FX1 type."""
        return self._data[TrackDataOffset.FX1_TYPE]

    @fx1_type.setter
    def fx1_type(self, value: int):
        self._data[TrackDataOffset.FX1_TYPE] = value
        # Apply FX type defaults
        if value in FX_DEFAULTS:
            offset = TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM1
            self._data[offset:offset + 6] = FX_DEFAULTS[value]

    @property
    def fx2_type(self) -> int:
        """Get/set the FX2 type."""
        return self._data[TrackDataOffset.FX2_TYPE]

    @fx2_type.setter
    def fx2_type(self, value: int):
        self._data[TrackDataOffset.FX2_TYPE] = value
        # Apply FX type defaults
        if value in FX_DEFAULTS:
            offset = TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM1
            self._data[offset:offset + 6] = FX_DEFAULTS[value]

    # === AMP page ===

    @property
    def attack(self) -> int:
        """Get/set amplitude attack (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_ATK]

    @attack.setter
    def attack(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_ATK] = value & 0x7F

    @property
    def hold(self) -> int:
        """Get/set amplitude hold (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_HOLD]

    @hold.setter
    def hold(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_HOLD] = value & 0x7F

    @property
    def release(self) -> int:
        """Get/set amplitude release (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_REL]

    @release.setter
    def release(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_REL] = value & 0x7F

    @property
    def amp_volume(self) -> int:
        """Get/set amplitude volume (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_VOL]

    @amp_volume.setter
    def amp_volume(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_VOL] = value & 0x7F

    @property
    def balance(self) -> int:
        """Get/set amplitude balance (0-127, 64 = center)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_BAL]

    @balance.setter
    def balance(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.AMP_BAL] = value & 0x7F

    # === Recorder ===

    @property
    def recorder(self) -> RecorderSetup:
        """Get recorder buffer configuration for this track."""
        return self._recorder

    @recorder.setter
    def recorder(self, value: RecorderSetup):
        """Set recorder buffer configuration."""
        self._recorder = value

    # === SRC/Playback page (Flex/Static) ===

    def _flex_values_offset(self) -> int:
        """Get offset for Flex playback params in buffer."""
        return TrackDataOffset.MACHINE_PARAMS_VALUES + MachineParamsOffset.FLEX

    def _flex_setup_offset(self) -> int:
        """Get offset for Flex setup params in buffer."""
        return TrackDataOffset.MACHINE_PARAMS_SETUP + MachineParamsOffset.FLEX

    @property
    def pitch(self) -> int:
        """Get/set pitch for Flex/Static (0-127, 64=center)."""
        return self._data[self._flex_values_offset() + FlexStaticParamsOffset.PTCH]

    @pitch.setter
    def pitch(self, value: int):
        self._data[self._flex_values_offset() + FlexStaticParamsOffset.PTCH] = value & 0x7F

    @property
    def start(self) -> int:
        """Get/set start point for Flex/Static (0-127)."""
        return self._data[self._flex_values_offset() + FlexStaticParamsOffset.STRT]

    @start.setter
    def start(self, value: int):
        self._data[self._flex_values_offset() + FlexStaticParamsOffset.STRT] = value & 0x7F

    @property
    def length(self) -> int:
        """Get/set length for Flex/Static (0-127)."""
        return self._data[self._flex_values_offset() + FlexStaticParamsOffset.LEN]

    @length.setter
    def length(self, value: int):
        self._data[self._flex_values_offset() + FlexStaticParamsOffset.LEN] = value & 0x7F

    @property
    def rate(self) -> int:
        """Get/set playback rate for Flex/Static (0-127)."""
        return self._data[self._flex_values_offset() + FlexStaticParamsOffset.RATE]

    @rate.setter
    def rate(self, value: int):
        self._data[self._flex_values_offset() + FlexStaticParamsOffset.RATE] = value & 0x7F

    # === Serialization ===

    def to_dict(self) -> dict:
        """Convert audio part track to dictionary."""
        return {
            "track": self._track_num,
            "machine_type": self.machine_type.name,
            "flex_slot": self.flex_slot,
            "static_slot": self.static_slot,
            "recorder_slot": self.recorder_slot,
            "volume": {"main": self.volume[0], "cue": self.volume[1]},
            "amp": {
                "attack": self.attack,
                "hold": self.hold,
                "release": self.release,
                "volume": self.amp_volume,
                "balance": self.balance,
            },
            "fx1_type": self.fx1_type,
            "fx2_type": self.fx2_type,
            "recorder": self._recorder.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudioPartTrack":
        """Create an AudioPartTrack from a dictionary."""
        kwargs = {
            "track_num": data.get("track", 1),
        }

        if "machine_type" in data:
            mt = data["machine_type"]
            kwargs["machine_type"] = MachineType[mt] if isinstance(mt, str) else MachineType(mt)

        if "flex_slot" in data:
            kwargs["flex_slot"] = data["flex_slot"]
        if "static_slot" in data:
            kwargs["static_slot"] = data["static_slot"]
        if "recorder_slot" in data:
            kwargs["recorder_slot"] = data["recorder_slot"]

        if "volume" in data:
            kwargs["main_volume"] = data["volume"].get("main", 108)
            kwargs["cue_volume"] = data["volume"].get("cue", 108)

        if "amp" in data:
            amp = data["amp"]
            kwargs["attack"] = amp.get("attack", 0)
            kwargs["hold"] = amp.get("hold", 127)
            kwargs["release"] = amp.get("release", 24)
            kwargs["amp_volume"] = amp.get("volume", 108)
            kwargs["balance"] = amp.get("balance", 64)

        if "fx1_type" in data:
            kwargs["fx1_type"] = data["fx1_type"]
        if "fx2_type" in data:
            kwargs["fx2_type"] = data["fx2_type"]

        if "recorder" in data:
            kwargs["recorder"] = RecorderSetup.from_dict(data["recorder"])

        return cls(**kwargs)

    def __eq__(self, other) -> bool:
        """Check equality based on data buffer and recorder."""
        if not isinstance(other, AudioPartTrack):
            return NotImplemented
        return (
            self._track_num == other._track_num
            and self._data == other._data
            and self._recorder == other._recorder
        )

    def __repr__(self) -> str:
        return f"AudioPartTrack(track={self._track_num}, machine_type={self.machine_type.name})"
