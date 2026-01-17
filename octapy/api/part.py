"""
Part and PartTrack classes for sound configuration.
"""

from abc import ABC
from typing import TYPE_CHECKING, Dict

from .._io import (
    PartOffset,
    MachineSlotOffset,
    MachineParamsOffset,
    FlexStaticParamsOffset,
    FlexStaticSetupOffset,
    ThruParamsOffset,
    PickupParamsOffset,
    PickupSetupOffset,
    MidiPartOffset,
    MidiTrackValuesOffset,
    MidiTrackSetupOffset,
    MACHINE_SLOT_SIZE,
    MACHINE_PARAMS_SIZE,
    MIDI_TRACK_VALUES_SIZE,
    MIDI_TRACK_SETUP_SIZE,
)
from .enums import MachineType, ThruInput

if TYPE_CHECKING:
    from .bank import Bank


# =============================================================================
# BasePartTrack Class
# =============================================================================

class BasePartTrack(ABC):
    """
    Abstract base class for part track configuration.

    Provides shared functionality for accessing part data.
    Subclasses provide track-specific properties.
    """

    def __init__(self, part: "Part", track_num: int):
        self._part = part
        self._track_num = track_num

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._part._bank._bank_file._data

    def _part_offset(self) -> int:
        """Get the byte offset for this track's part in the bank file."""
        return self._part._bank._bank_file.part_offset(self._part._part_num)


# =============================================================================
# AudioPartTrack Class
# =============================================================================

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


# =============================================================================
# SamplerPartTrack Class (Base for Flex/Static)
# =============================================================================

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


# =============================================================================
# FlexPartTrack Class
# =============================================================================

class FlexPartTrack(SamplerPartTrack):
    """
    Flex machine track configuration.

    Flex machines load samples into RAM for manipulation.
    See SamplerPartTrack for encoder layout documentation.

    Usage:
        track = part.flex_track(1)
        track.pitch = 64          # No transpose
        track.start = 0           # Sample start
        track.retrig_time = 79    # Retrig time (default)
    """

    def _values_offset(self) -> int:
        """Get offset for Flex params values."""
        return self._machine_params_values_offset(MachineParamsOffset.FLEX)

    def _setup_offset(self) -> int:
        """Get offset for Flex params setup."""
        return self._machine_params_setup_offset(MachineParamsOffset.FLEX)


# =============================================================================
# StaticPartTrack Class
# =============================================================================

class StaticPartTrack(SamplerPartTrack):
    """
    Static machine track configuration.

    Static machines stream samples from the CF card.
    See SamplerPartTrack for encoder layout documentation.

    Usage:
        track = part.static_track(1)
        track.pitch = 64
        track.start = 0
    """

    def _values_offset(self) -> int:
        """Get offset for Static params values."""
        return self._machine_params_values_offset(MachineParamsOffset.STATIC)

    def _setup_offset(self) -> int:
        """Get offset for Static params setup."""
        return self._machine_params_setup_offset(MachineParamsOffset.STATIC)


# =============================================================================
# ThruPartTrack Class
# =============================================================================

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


# =============================================================================
# NeighborPartTrack Class
# =============================================================================

class NeighborPartTrack(AudioPartTrack):
    """
    Neighbor machine track configuration.

    Neighbor machines route audio from adjacent tracks.
    The SRC page has no active encoders - all parameters are unused.

    SRC Page Encoders:
        A-F: (all unused)

    Usage:
        track = part.neighbor_track(1)
        # No machine-specific params - just uses base AudioPartTrack features
        # (machine_type, volume, fx1_type, fx2_type, etc.)
    """
    pass


# =============================================================================
# PickupPartTrack Class
# =============================================================================

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


# =============================================================================
# MidiPartTrack Class
# =============================================================================

class MidiPartTrack(BasePartTrack):
    """
    MIDI track configuration within a Part.

    Provides access to MIDI channel, program, and default note parameters.
    This is separate from MidiPatternTrack which handles sequencing.

    NOTE Page Encoders:
        A: NOTE (note)            - default_note property
        B: VEL (velocity)         - default_velocity property
        C: LEN (length)           - default_length property
        D: NOT2 (note 2)          - default_note2 property (chord)
        E: NOT3 (note 3)          - default_note3 property (chord)
        F: NOT4 (note 4)          - default_note4 property (chord)

    Note2/3/4 are chord note offsets (64 = no offset, <64 = lower, >64 = higher).

    Usage:
        midi_track = part.midi_track(1)
        midi_track.channel = 5           # MIDI channel 6 (0-indexed)
        midi_track.program = 32          # Program 33
        midi_track.default_note = 60     # Middle C
        midi_track.default_note2 = 67    # +7 semitones (G)
    """

    def _values_offset(self) -> int:
        """Get byte offset for this track's MidiTrackParamsValues."""
        return (self._part_offset() +
                MidiPartOffset.MIDI_TRACK_PARAMS_VALUES +
                (self._track_num - 1) * MIDI_TRACK_VALUES_SIZE)

    def _setup_offset(self) -> int:
        """Get byte offset for this track's MidiTrackParamsSetup."""
        return (self._part_offset() +
                MidiPartOffset.MIDI_TRACK_PARAMS_SETUP +
                (self._track_num - 1) * MIDI_TRACK_SETUP_SIZE)

    # === Setup properties (MidiTrackNoteParamsSetup) ===

    @property
    def channel(self) -> int:
        """Get/set the MIDI channel (0-15)."""
        return self._data[self._setup_offset() + MidiTrackSetupOffset.CHANNEL]

    @channel.setter
    def channel(self, value: int):
        self._data[self._setup_offset() + MidiTrackSetupOffset.CHANNEL] = value & 0x0F

    @property
    def bank(self) -> int:
        """Get/set the bank select (128 = off)."""
        return self._data[self._setup_offset() + MidiTrackSetupOffset.BANK]

    @bank.setter
    def bank(self, value: int):
        self._data[self._setup_offset() + MidiTrackSetupOffset.BANK] = value & 0xFF

    @property
    def program(self) -> int:
        """Get/set the program change (128 = off)."""
        return self._data[self._setup_offset() + MidiTrackSetupOffset.PROGRAM]

    @program.setter
    def program(self, value: int):
        self._data[self._setup_offset() + MidiTrackSetupOffset.PROGRAM] = value & 0xFF

    # === Values properties (MidiTrackMidiParamsValues) ===

    @property
    def default_note(self) -> int:
        """Get/set the default note (0-127, 48 = C3)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.NOTE]

    @default_note.setter
    def default_note(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.NOTE] = value & 0x7F

    @property
    def default_velocity(self) -> int:
        """Get/set the default velocity (0-127)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.VELOCITY]

    @default_velocity.setter
    def default_velocity(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.VELOCITY] = value & 0x7F

    @property
    def default_length(self) -> int:
        """Get/set the default note length (6 = 1/16)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.LENGTH]

    @default_length.setter
    def default_length(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.LENGTH] = value & 0xFF

    @property
    def default_note2(self) -> int:
        """Get/set the default note 2 for chords (0-127, 64 = no offset)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.NOTE2]

    @default_note2.setter
    def default_note2(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.NOTE2] = value & 0x7F

    @property
    def default_note3(self) -> int:
        """Get/set the default note 3 for chords (0-127, 64 = no offset)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.NOTE3]

    @default_note3.setter
    def default_note3(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.NOTE3] = value & 0x7F

    @property
    def default_note4(self) -> int:
        """Get/set the default note 4 for chords (0-127, 64 = no offset)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.NOTE4]

    @default_note4.setter
    def default_note4(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.NOTE4] = value & 0x7F

    # === CC Number Assignments (Setup) ===

    def cc_number(self, n: int) -> int:
        """
        Get the MIDI CC number assigned to slot n (1-10).

        Args:
            n: CC slot number (1-10)

        Returns:
            MIDI CC number (0-127)
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = self._setup_offset() + 19 + n  # CC1 is at offset 20
        return self._data[offset]

    def set_cc_number(self, n: int, value: int):
        """
        Set the MIDI CC number assigned to slot n (1-10).

        Args:
            n: CC slot number (1-10)
            value: MIDI CC number (0-127)
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = self._setup_offset() + 19 + n  # CC1 is at offset 20
        self._data[offset] = value & 0x7F

    # === CC Default Values ===

    @property
    def pitch_bend(self) -> int:
        """Get/set default pitch bend (0-127, 64 = center)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.PITCH_BEND]

    @pitch_bend.setter
    def pitch_bend(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.PITCH_BEND] = value & 0x7F

    @property
    def aftertouch(self) -> int:
        """Get/set default aftertouch (0-127)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.AFTERTOUCH]

    @aftertouch.setter
    def aftertouch(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.AFTERTOUCH] = value & 0x7F

    def cc_value(self, n: int) -> int:
        """
        Get the default value for CC slot n (1-10).

        Args:
            n: CC slot number (1-10)

        Returns:
            Default CC value (0-127)
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = self._values_offset() + 19 + n  # CC1 is at offset 20
        return self._data[offset]

    def set_cc_value(self, n: int, value: int):
        """
        Set the default value for CC slot n (1-10).

        Args:
            n: CC slot number (1-10)
            value: Default CC value (0-127)
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = self._values_offset() + 19 + n  # CC1 is at offset 20
        self._data[offset] = value & 0x7F


# =============================================================================
# Part Class
# =============================================================================

class Part:
    """
    Pythonic interface for an Octatrack Part.

    A Part holds machine configurations for all 8 tracks.
    Each bank has 4 parts.

    Usage:
        part = bank.part(1)

        # Generic track access (base AudioPartTrack)
        track = part.track(1)
        track.machine_type = MachineType.FLEX

        # Machine-specific access with typed properties
        flex = part.flex_track(1)
        flex.pitch = 64
        flex.timestretch = 0
    """

    def __init__(self, bank: "Bank", part_num: int):
        self._bank = bank
        self._part_num = part_num
        self._tracks: Dict[int, AudioPartTrack] = {}
        self._flex_tracks: Dict[int, FlexPartTrack] = {}
        self._static_tracks: Dict[int, StaticPartTrack] = {}
        self._thru_tracks: Dict[int, ThruPartTrack] = {}
        self._neighbor_tracks: Dict[int, NeighborPartTrack] = {}
        self._pickup_tracks: Dict[int, PickupPartTrack] = {}
        self._midi_tracks: Dict[int, MidiPartTrack] = {}

    def _part_offset(self) -> int:
        """Get the byte offset for this part in the bank file."""
        return self._bank._bank_file.part_offset(self._part_num)

    def track(self, track_num: int) -> AudioPartTrack:
        """
        Get a track (1-8) as base AudioPartTrack.

        For machine-specific parameters, use flex_track(), static_track(), etc.

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioPartTrack instance for configuring machine settings
        """
        if track_num not in self._tracks:
            self._tracks[track_num] = AudioPartTrack(self, track_num)
        return self._tracks[track_num]

    def flex_track(self, track_num: int) -> FlexPartTrack:
        """
        Get a track (1-8) as FlexPartTrack with Flex-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            FlexPartTrack instance with pitch, start, length, rate, etc.
        """
        if track_num not in self._flex_tracks:
            self._flex_tracks[track_num] = FlexPartTrack(self, track_num)
        return self._flex_tracks[track_num]

    def static_track(self, track_num: int) -> StaticPartTrack:
        """
        Get a track (1-8) as StaticPartTrack with Static-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            StaticPartTrack instance with pitch, start, length, rate, etc.
        """
        if track_num not in self._static_tracks:
            self._static_tracks[track_num] = StaticPartTrack(self, track_num)
        return self._static_tracks[track_num]

    def thru_track(self, track_num: int) -> ThruPartTrack:
        """
        Get a track (1-8) as ThruPartTrack with Thru-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            ThruPartTrack instance with in_ab, vol_ab, in_cd, vol_cd
        """
        if track_num not in self._thru_tracks:
            self._thru_tracks[track_num] = ThruPartTrack(self, track_num)
        return self._thru_tracks[track_num]

    def neighbor_track(self, track_num: int) -> NeighborPartTrack:
        """
        Get a track (1-8) as NeighborPartTrack.

        Neighbor machines have no machine-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            NeighborPartTrack instance
        """
        if track_num not in self._neighbor_tracks:
            self._neighbor_tracks[track_num] = NeighborPartTrack(self, track_num)
        return self._neighbor_tracks[track_num]

    def pickup_track(self, track_num: int) -> PickupPartTrack:
        """
        Get a track (1-8) as PickupPartTrack with Pickup-specific parameters.

        Args:
            track_num: Track number (1-8)

        Returns:
            PickupPartTrack instance with pitch, direction, gain, operation, etc.
        """
        if track_num not in self._pickup_tracks:
            self._pickup_tracks[track_num] = PickupPartTrack(self, track_num)
        return self._pickup_tracks[track_num]

    def midi_track(self, track_num: int) -> MidiPartTrack:
        """
        Get MIDI configuration for a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPartTrack instance for configuring MIDI settings
        """
        if track_num not in self._midi_tracks:
            self._midi_tracks[track_num] = MidiPartTrack(self, track_num)
        return self._midi_tracks[track_num]

    @property
    def active_scene_a(self) -> int:
        """Get/set active scene A (0-15)."""
        data = self._bank._bank_file._data
        return data[self._part_offset() + PartOffset.ACTIVE_SCENE_A]

    @active_scene_a.setter
    def active_scene_a(self, value: int):
        data = self._bank._bank_file._data
        data[self._part_offset() + PartOffset.ACTIVE_SCENE_A] = value & 0x0F

    @property
    def active_scene_b(self) -> int:
        """Get/set active scene B (0-15)."""
        data = self._bank._bank_file._data
        return data[self._part_offset() + PartOffset.ACTIVE_SCENE_B]

    @active_scene_b.setter
    def active_scene_b(self, value: int):
        data = self._bank._bank_file._data
        data[self._part_offset() + PartOffset.ACTIVE_SCENE_B] = value & 0x0F
