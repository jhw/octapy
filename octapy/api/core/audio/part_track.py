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
    AudioTrackParamsOffset,
    MACHINE_SLOT_SIZE,
    MACHINE_PARAMS_SIZE,
    AUDIO_TRACK_PARAMS_SIZE,
    RECORDER_SETUP_SIZE,
    FX_DEFAULTS,
    # Template (machine) defaults
    TEMPLATE_DEFAULT_SRC_VALUES,
    TEMPLATE_DEFAULT_SRC_SETUP,
    TEMPLATE_DEFAULT_AMP,
    TEMPLATE_DEFAULT_FX1_PARAMS,
    TEMPLATE_DEFAULT_FX2_PARAMS,
    TEMPLATE_DEFAULT_FX1_TYPE,
    TEMPLATE_DEFAULT_FX2_TYPE,
    # Octapy recommended defaults (length=127, length_mode=TIME)
    OCTAPY_DEFAULT_SRC_VALUES,
    OCTAPY_DEFAULT_SRC_SETUP,
)
from ...enums import MachineType, FX1Type, FX2Type
from .recorder import AudioRecorderSetup
from .._page import PageAccessor, SRC_PARAM_NAMES, SRC_SETUP_PARAM_NAMES, AMP_PARAM_NAMES, FX_PARAM_NAMES, _AMP_KEY


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
        recorder_slot: Optional[int] = None,
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
        # Recorder (can pass AudioRecorderSetup or individual args)
        recorder: Optional[AudioRecorderSetup] = None,
    ):
        """
        Create an AudioPartTrack with optional parameter overrides.

        Args:
            track_num: Track number (1-8)
            machine_type: Machine type (FLEX, STATIC, THRU, NEIGHBOR, PICKUP)
            flex_slot: Flex sample slot (0-127 for sample slots 1-128)
            static_slot: Static sample slot (0-127)
            recorder_slot: Recorder buffer for playback (0-7 for buffers 1-8).
                          Mutually exclusive with flex_slot - setting this
                          overrides flex_slot for Flex machine playback.
            main_volume: Main output volume (0-127)
            cue_volume: Cue output volume (0-127)
            fx1_type: FX1 effect type
            fx2_type: FX2 effect type
            attack: AMP attack (0-127)
            hold: AMP hold (0-127)
            release: AMP release (0-127)
            amp_volume: AMP volume (0-127)
            balance: AMP balance (0-127, 64=center)
            recorder: AudioRecorderSetup object (or created with defaults)
        """
        self._track_num = track_num
        self._data = bytearray(AUDIO_PART_TRACK_SIZE)

        # Apply defaults
        self._apply_defaults()

        # Apply constructor arguments
        self.machine_type = machine_type
        self.static_slot = static_slot
        # flex_slot and recorder_slot are mutually exclusive (both write to FLEX_SLOT_ID)
        # recorder_slot takes precedence if set
        if recorder_slot is not None:
            self.recorder_slot = recorder_slot
        else:
            self.flex_slot = flex_slot
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
            self._recorder = AudioRecorderSetup()

    def _apply_defaults(self):
        """Apply template (machine) default values to the buffer."""
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

        # Machine params values - apply template SRC defaults for FLEX
        offset = TrackDataOffset.MACHINE_PARAMS_VALUES + MachineParamsOffset.FLEX
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_SRC_VALUES

        # Machine params setup - apply template SRC defaults for FLEX
        offset = TrackDataOffset.MACHINE_PARAMS_SETUP + MachineParamsOffset.FLEX
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_SRC_SETUP

        # Track params - AMP defaults
        offset = TrackDataOffset.TRACK_PARAMS
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_AMP

        # FX1 params
        offset = TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM1
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_FX1_PARAMS

        # FX2 params
        offset = TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM1
        self._data[offset:offset + 6] = TEMPLATE_DEFAULT_FX2_PARAMS

        # Recorder setup will be handled by AudioRecorderSetup object

    @classmethod
    def flex_with_recommended_defaults(
        cls,
        track_num: int = 1,
        flex_slot: int = 0,
        **kwargs,
    ) -> "AudioPartTrack":
        """
        Create a Flex machine track with octapy recommended defaults.

        Recommended defaults differ from OT machine defaults:
        - length = 127 (full sample length, vs OT default 0)
        - length_mode = TIME (vs OT default OFF)
        - loop = OFF (vs OT default ON)

        These settings are optimized for one-shot sample playback.

        Args:
            track_num: Track number (1-8)
            flex_slot: Flex sample slot (0-127)
            **kwargs: Additional arguments passed to AudioPartTrack constructor

        Returns:
            AudioPartTrack configured as Flex with recommended defaults
        """
        track = cls(
            track_num=track_num,
            machine_type=MachineType.FLEX,
            flex_slot=flex_slot,
            **kwargs,
        )
        track.apply_recommended_flex_defaults()
        return track

    def apply_recommended_flex_defaults(self):
        """
        Apply octapy recommended defaults for Flex machine SRC page.

        Sets:
        - length = 127 (full sample length)
        - length_mode = TIME
        - loop = OFF

        These differ from OT machine defaults and are optimized for
        one-shot sample playback.

        Note: Only affects FLEX machine parameters. Call this after
        setting machine_type to FLEX.
        """
        # Apply octapy recommended SRC values (includes length=127)
        offset = TrackDataOffset.MACHINE_PARAMS_VALUES + MachineParamsOffset.FLEX
        self._data[offset:offset + 6] = OCTAPY_DEFAULT_SRC_VALUES

        # Apply octapy recommended SRC setup (includes length_mode=TIME, loop=OFF)
        offset = TrackDataOffset.MACHINE_PARAMS_SETUP + MachineParamsOffset.FLEX
        self._data[offset:offset + 6] = OCTAPY_DEFAULT_SRC_SETUP

    def configure_as_recorder(self, source: "RecordingSource") -> None:
        """
        Configure this track as a one-shot recorder buffer player.

        Sets up the classic Octatrack recording pattern:
        - Flex machine playing this track's own recorder buffer
        - Recorder source set to the specified source (typically another track or MAIN)
        - Recommended Flex defaults applied (length=127, length_mode=TIME, loop=OFF)

        The recorder buffer number matches the track number (track 3 -> buffer 3).

        Args:
            source: What to record from (e.g. RecordingSource.TRACK_5,
                    RecordingSource.MAIN, RecordingSource.INPUT_AB)

        Usage:
            # Track 3 records from track 2's output
            part.track(3).configure_as_recorder(RecordingSource.TRACK_2)

            # Track 7 records the master output
            part.track(7).configure_as_recorder(RecordingSource.MAIN)
        """
        from ...enums import RecordingSource as _RS

        if not isinstance(source, _RS):
            raise TypeError(f"source must be a RecordingSource, got {type(source).__name__}")

        self.machine_type = MachineType.FLEX
        self.recorder_slot = self._track_num - 1  # Track N -> buffer N (0-indexed)
        self.apply_recommended_flex_defaults()
        self.recorder.source = source

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

        # Read recorder setup into AudioRecorderSetup object
        offset = part_offset + PartOffset.RECORDER_SETUP + track_idx * RECORDER_SETUP_SIZE
        instance._recorder = AudioRecorderSetup.read(part_data[offset:offset + RECORDER_SETUP_SIZE])

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
    #
    # The Octatrack's flex_slots array has 136 entries:
    # - Indices 0-127: sample slots (1-128 in user-facing 1-indexed terms)
    # - Indices 128-135: recorder buffers (1-8 in user-facing terms)
    #
    # For Flex machine playback, FLEX_SLOT_ID determines what plays:
    # - Values 0-127: play from sample slot
    # - Values 128-135: play from recorder buffer
    #
    # flex_slot and recorder_slot are mutually exclusive views into the same
    # underlying byte (FLEX_SLOT_ID). Setting one overrides the other.

    @property
    def flex_slot(self) -> int:
        """
        Get/set the flex sample slot (0-127 for sample slots 1-128).

        This is mutually exclusive with recorder_slot - both write to the
        same underlying byte. Setting flex_slot clears any recorder_slot setting.

        Returns:
            The sample slot index (0-127), or the raw value if >= 128
            (indicating recorder_slot is set instead).
        """
        return self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.FLEX_SLOT_ID]

    @flex_slot.setter
    def flex_slot(self, value: int):
        if not 0 <= value <= 127:
            raise ValueError(f"flex_slot must be 0-127, got {value}")
        self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.FLEX_SLOT_ID] = value

    @property
    def static_slot(self) -> int:
        """Get/set the static sample slot."""
        return self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.STATIC_SLOT_ID]

    @static_slot.setter
    def static_slot(self, value: int):
        self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.STATIC_SLOT_ID] = value & 0xFF

    @property
    def recorder_slot(self) -> Optional[int]:
        """
        Get/set the recorder buffer for Flex machine playback (0-7 for buffers 1-8).

        This is mutually exclusive with flex_slot - both write to the same
        underlying byte (FLEX_SLOT_ID). Setting recorder_slot overrides flex_slot.

        Recorder buffers occupy slots 128-135 in the unified flex_slots array.
        This property provides a clean interface using buffer indices 0-7.

        Returns:
            The recorder buffer index (0-7), or None if flex_slot is set instead.
        """
        val = self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.FLEX_SLOT_ID]
        if val >= 128:
            return val - 128
        return None

    @recorder_slot.setter
    def recorder_slot(self, value: int):
        if not 0 <= value <= 7:
            raise ValueError(f"recorder_slot must be 0-7, got {value}")
        self._data[TrackDataOffset.MACHINE_SLOTS + MachineSlotOffset.FLEX_SLOT_ID] = 128 + value

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

    # === FX1 params ===

    @property
    def fx1_param1(self) -> int:
        """Get/set FX1 parameter 1 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM1]

    @fx1_param1.setter
    def fx1_param1(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM1] = value & 0x7F

    @property
    def fx1_param2(self) -> int:
        """Get/set FX1 parameter 2 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM2]

    @fx1_param2.setter
    def fx1_param2(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM2] = value & 0x7F

    @property
    def fx1_param3(self) -> int:
        """Get/set FX1 parameter 3 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM3]

    @fx1_param3.setter
    def fx1_param3(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM3] = value & 0x7F

    @property
    def fx1_param4(self) -> int:
        """Get/set FX1 parameter 4 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM4]

    @fx1_param4.setter
    def fx1_param4(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM4] = value & 0x7F

    @property
    def fx1_param5(self) -> int:
        """Get/set FX1 parameter 5 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM5]

    @fx1_param5.setter
    def fx1_param5(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM5] = value & 0x7F

    @property
    def fx1_param6(self) -> int:
        """Get/set FX1 parameter 6 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM6]

    @fx1_param6.setter
    def fx1_param6(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX1_PARAM6] = value & 0x7F

    # === FX2 params ===

    @property
    def fx2_param1(self) -> int:
        """Get/set FX2 parameter 1 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM1]

    @fx2_param1.setter
    def fx2_param1(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM1] = value & 0x7F

    @property
    def fx2_param2(self) -> int:
        """Get/set FX2 parameter 2 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM2]

    @fx2_param2.setter
    def fx2_param2(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM2] = value & 0x7F

    @property
    def fx2_param3(self) -> int:
        """Get/set FX2 parameter 3 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM3]

    @fx2_param3.setter
    def fx2_param3(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM3] = value & 0x7F

    @property
    def fx2_param4(self) -> int:
        """Get/set FX2 parameter 4 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM4]

    @fx2_param4.setter
    def fx2_param4(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM4] = value & 0x7F

    @property
    def fx2_param5(self) -> int:
        """Get/set FX2 parameter 5 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM5]

    @fx2_param5.setter
    def fx2_param5(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM5] = value & 0x7F

    @property
    def fx2_param6(self) -> int:
        """Get/set FX2 parameter 6 (0-127)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM6]

    @fx2_param6.setter
    def fx2_param6(self, value: int):
        self._data[TrackDataOffset.TRACK_PARAMS + AudioTrackParamsOffset.FX2_PARAM6] = value & 0x7F

    # === FX Accessors (named parameter access) ===

    @property
    def fx1(self) -> PageAccessor:
        """
        FX1 page accessor. Names depend on FX type.

        Usage:
            track.fx1.base = 64      # FX1Type.FILTER param1
            track.fx1.delay = 64     # FX1Type.CHORUS param1
        """
        if not hasattr(self, '_fx1_accessor'):
            self._fx1_accessor = PageAccessor(
                page_name='FX1',
                param_names_map=FX_PARAM_NAMES,
                get_type=lambda: self.fx1_type,
                get_param=lambda n: getattr(self, f'fx1_param{n}'),
                set_param=lambda n, v: setattr(self, f'fx1_param{n}', v),
            )
        return self._fx1_accessor

    @property
    def fx2(self) -> PageAccessor:
        """
        FX2 page accessor. Names depend on FX type.

        Usage:
            track.fx2.time = 64      # FX2Type.DELAY param1
            track.fx2.mix = 100      # FX2Type.PLATE_REVERB param6
        """
        if not hasattr(self, '_fx2_accessor'):
            self._fx2_accessor = PageAccessor(
                page_name='FX2',
                param_names_map=FX_PARAM_NAMES,
                get_type=lambda: self.fx2_type,
                get_param=lambda n: getattr(self, f'fx2_param{n}'),
                set_param=lambda n, v: setattr(self, f'fx2_param{n}', v),
            )
        return self._fx2_accessor

    # === AMP page (deprecated bare properties — use track.amp.* instead) ===

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
    def recorder(self) -> AudioRecorderSetup:
        """Get recorder buffer configuration for this track."""
        return self._recorder

    @recorder.setter
    def recorder(self, value: AudioRecorderSetup):
        """Set recorder buffer configuration."""
        self._recorder = value

    # === SRC/Playback page ===

    # Machine type to params offset mapping
    _MACHINE_PARAMS_OFFSET = {
        MachineType.STATIC: MachineParamsOffset.STATIC,
        MachineType.FLEX: MachineParamsOffset.FLEX,
        MachineType.THRU: MachineParamsOffset.THRU,
        MachineType.NEIGHBOR: MachineParamsOffset.NEIGHBOR,
        MachineType.PICKUP: MachineParamsOffset.PICKUP,
    }

    def _machine_values_offset(self) -> int:
        """Get offset for current machine's playback params in buffer."""
        offset = self._MACHINE_PARAMS_OFFSET.get(self.machine_type, MachineParamsOffset.FLEX)
        return TrackDataOffset.MACHINE_PARAMS_VALUES + offset

    def _machine_setup_offset(self) -> int:
        """Get offset for current machine's setup params in buffer."""
        offset = self._MACHINE_PARAMS_OFFSET.get(self.machine_type, MachineParamsOffset.FLEX)
        return TrackDataOffset.MACHINE_PARAMS_SETUP + offset

    def _get_playback_param(self, n: int) -> int:
        """Get playback param n (1-6) for current machine type."""
        return self._data[self._machine_values_offset() + (n - 1)]

    def _set_playback_param(self, n: int, value: int):
        """Set playback param n (1-6) for current machine type."""
        self._data[self._machine_values_offset() + (n - 1)] = value & 0x7F

    def _get_setup_param(self, n: int) -> int:
        """Get setup param n (1-6) for current machine type."""
        return self._data[self._machine_setup_offset() + (n - 1)]

    def _set_setup_param(self, n: int, value: int):
        """Set setup param n (1-6) for current machine type."""
        self._data[self._machine_setup_offset() + (n - 1)] = value & 0x7F

    # AMP param indices: 1=attack, 2=hold, 3=release, 4=volume, 5=balance
    _AMP_OFFSETS = (
        AudioTrackParamsOffset.AMP_ATK,
        AudioTrackParamsOffset.AMP_HOLD,
        AudioTrackParamsOffset.AMP_REL,
        AudioTrackParamsOffset.AMP_VOL,
        AudioTrackParamsOffset.AMP_BAL,
    )

    def _get_amp_param(self, n: int) -> int:
        """Get AMP param n (1=attack, 2=hold, 3=release, 4=volume, 5=balance)."""
        return self._data[TrackDataOffset.TRACK_PARAMS + self._AMP_OFFSETS[n - 1]]

    def _set_amp_param(self, n: int, value: int):
        """Set AMP param n (1=attack, 2=hold, 3=release, 4=volume, 5=balance)."""
        self._data[TrackDataOffset.TRACK_PARAMS + self._AMP_OFFSETS[n - 1]] = value & 0x7F

    @property
    def src(self) -> PageAccessor:
        """
        SRC playback page accessor. Names depend on machine type.

        Usage:
            track.src.pitch = 64         # Flex/Static param1
            track.src.in_ab = 1          # Thru param1
        """
        if not hasattr(self, '_src_accessor'):
            self._src_accessor = PageAccessor(
                page_name='SRC',
                param_names_map=SRC_PARAM_NAMES,
                get_type=lambda: self.machine_type,
                get_param=self._get_playback_param,
                set_param=self._set_playback_param,
            )
        return self._src_accessor

    @property
    def setup(self) -> PageAccessor:
        """
        SRC setup page accessor. Names depend on machine type.

        Usage:
            track.setup.loop = 0              # Flex/Static: loop off
            track.setup.length_mode = 1       # Flex/Static: TIME mode
            track.setup.timestretch = 1       # Flex/Static: AUTO
        """
        if not hasattr(self, '_setup_accessor'):
            self._setup_accessor = PageAccessor(
                page_name='setup',
                param_names_map=SRC_SETUP_PARAM_NAMES,
                get_type=lambda: self.machine_type,
                get_param=self._get_setup_param,
                set_param=self._set_setup_param,
            )
        return self._setup_accessor

    @property
    def amp(self) -> PageAccessor:
        """
        AMP page accessor. Fixed names for all machine types.

        Usage:
            track.amp.attack = 10
            track.amp.volume = 108
            track.amp.balance = 64
        """
        if not hasattr(self, '_amp_accessor'):
            self._amp_accessor = PageAccessor(
                page_name='AMP',
                param_names_map=AMP_PARAM_NAMES,
                get_type=lambda: _AMP_KEY,
                get_param=self._get_amp_param,
                set_param=self._set_amp_param,
            )
        return self._amp_accessor

    # === Serialization ===

    def to_dict(self) -> dict:
        """Convert audio part track to dictionary."""
        result = {
            "track": self._track_num,
            "machine_type": self.machine_type.name,
            "static_slot": self.static_slot,
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
        # flex_slot and recorder_slot are mutually exclusive
        rec_slot = self.recorder_slot
        if rec_slot is not None:
            result["recorder_slot"] = rec_slot
        else:
            result["flex_slot"] = self.flex_slot
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AudioPartTrack":
        """Create an AudioPartTrack from a dictionary."""
        kwargs = {
            "track_num": data.get("track", 1),
        }

        if "machine_type" in data:
            mt = data["machine_type"]
            kwargs["machine_type"] = MachineType[mt] if isinstance(mt, str) else MachineType(mt)

        # flex_slot and recorder_slot are mutually exclusive
        # recorder_slot takes precedence if both are present
        if "recorder_slot" in data:
            kwargs["recorder_slot"] = data["recorder_slot"]
        elif "flex_slot" in data:
            kwargs["flex_slot"] = data["flex_slot"]

        if "static_slot" in data:
            kwargs["static_slot"] = data["static_slot"]

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
            kwargs["recorder"] = AudioRecorderSetup.from_dict(data["recorder"])

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
