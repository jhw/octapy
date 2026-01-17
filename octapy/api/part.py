"""
Part and AudioPartTrack classes for sound configuration.
"""

from typing import TYPE_CHECKING, Dict

from .._io import (
    PartOffset,
    MachineSlotOffset,
    MidiPartOffset,
    MidiTrackValuesOffset,
    MidiTrackSetupOffset,
    MACHINE_SLOT_SIZE,
    MIDI_TRACK_VALUES_SIZE,
    MIDI_TRACK_SETUP_SIZE,
)
from .enums import MachineType

if TYPE_CHECKING:
    from .bank import Bank


class AudioPartTrack:
    """
    Audio track configuration within a Part.

    Provides access to machine type, sample slots, and track settings.
    This is separate from AudioPatternTrack which handles sequencing.

    Usage:
        track = part.track(1)
        track.machine_type = MachineType.FLEX
        track.flex_slot = 0
    """

    def __init__(self, part: "Part", track_num: int):
        self._part = part
        self._track_num = track_num

    def _part_offset(self) -> int:
        """Get the byte offset for this track's part in the bank file."""
        return self._part._bank._bank_file.part_offset(self._part._part_num)

    @property
    def machine_type(self) -> MachineType:
        """Get/set the machine type for this track."""
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_TYPES + (self._track_num - 1)
        return MachineType(data[offset])

    @machine_type.setter
    def machine_type(self, value: MachineType):
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_TYPES + (self._track_num - 1)
        data[offset] = int(value)

    @property
    def flex_slot(self) -> int:
        """Get/set the flex sample slot."""
        data = self._part._bank._bank_file._data
        slot_offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE
        return data[slot_offset + MachineSlotOffset.FLEX_SLOT_ID]

    @flex_slot.setter
    def flex_slot(self, value: int):
        data = self._part._bank._bank_file._data
        slot_offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE
        data[slot_offset + MachineSlotOffset.FLEX_SLOT_ID] = value & 0xFF

    @property
    def static_slot(self) -> int:
        """Get/set the static sample slot."""
        data = self._part._bank._bank_file._data
        slot_offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE
        return data[slot_offset + MachineSlotOffset.STATIC_SLOT_ID]

    @static_slot.setter
    def static_slot(self, value: int):
        data = self._part._bank._bank_file._data
        slot_offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE
        data[slot_offset + MachineSlotOffset.STATIC_SLOT_ID] = value & 0xFF

    @property
    def recorder_slot(self) -> int:
        """Get/set the recorder slot."""
        data = self._part._bank._bank_file._data
        slot_offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE
        return data[slot_offset + MachineSlotOffset.RECORDER_SLOT_ID]

    @recorder_slot.setter
    def recorder_slot(self, value: int):
        data = self._part._bank._bank_file._data
        slot_offset = self._part_offset() + PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (self._track_num - 1) * MACHINE_SLOT_SIZE
        data[slot_offset + MachineSlotOffset.RECORDER_SLOT_ID] = value & 0xFF

    @property
    def volume(self) -> tuple:
        """Get the volume as (main, cue) tuple."""
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_VOLUMES + (self._track_num - 1) * 2
        return (data[offset], data[offset + 1])

    def set_volume(self, main: int = 108, cue: int = 108):
        """Set the volume (main and cue)."""
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_VOLUMES + (self._track_num - 1) * 2
        data[offset] = main & 0x7F
        data[offset + 1] = cue & 0x7F

    @property
    def fx1_type(self) -> int:
        """Get/set the FX1 type."""
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX1 + (self._track_num - 1)
        return data[offset]

    @fx1_type.setter
    def fx1_type(self, value: int):
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX1 + (self._track_num - 1)
        data[offset] = value

    @property
    def fx2_type(self) -> int:
        """Get/set the FX2 type."""
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX2 + (self._track_num - 1)
        return data[offset]

    @fx2_type.setter
    def fx2_type(self, value: int):
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_FX2 + (self._track_num - 1)
        data[offset] = value


class MidiPartTrack:
    """
    MIDI track configuration within a Part.

    Provides access to MIDI channel, program, and default note parameters.
    This is separate from MidiPatternTrack which handles sequencing.

    Usage:
        midi_track = part.midi_track(1)
        midi_track.channel = 5           # MIDI channel 6 (0-indexed)
        midi_track.program = 32          # Program 33
        midi_track.default_note = 60     # Middle C
    """

    def __init__(self, part: "Part", track_num: int):
        self._part = part
        self._track_num = track_num

    def _part_offset(self) -> int:
        """Get the byte offset for this track's part in the bank file."""
        return self._part._bank._bank_file.part_offset(self._part._part_num)

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
        data = self._part._bank._bank_file._data
        return data[self._setup_offset() + MidiTrackSetupOffset.CHANNEL]

    @channel.setter
    def channel(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._setup_offset() + MidiTrackSetupOffset.CHANNEL] = value & 0x0F

    @property
    def bank(self) -> int:
        """Get/set the bank select (128 = off)."""
        data = self._part._bank._bank_file._data
        return data[self._setup_offset() + MidiTrackSetupOffset.BANK]

    @bank.setter
    def bank(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._setup_offset() + MidiTrackSetupOffset.BANK] = value & 0xFF

    @property
    def program(self) -> int:
        """Get/set the program change (128 = off)."""
        data = self._part._bank._bank_file._data
        return data[self._setup_offset() + MidiTrackSetupOffset.PROGRAM]

    @program.setter
    def program(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._setup_offset() + MidiTrackSetupOffset.PROGRAM] = value & 0xFF

    # === Values properties (MidiTrackMidiParamsValues) ===

    @property
    def default_note(self) -> int:
        """Get/set the default note (0-127, 48 = C3)."""
        data = self._part._bank._bank_file._data
        return data[self._values_offset() + MidiTrackValuesOffset.NOTE]

    @default_note.setter
    def default_note(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._values_offset() + MidiTrackValuesOffset.NOTE] = value & 0x7F

    @property
    def default_velocity(self) -> int:
        """Get/set the default velocity (0-127)."""
        data = self._part._bank._bank_file._data
        return data[self._values_offset() + MidiTrackValuesOffset.VELOCITY]

    @default_velocity.setter
    def default_velocity(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._values_offset() + MidiTrackValuesOffset.VELOCITY] = value & 0x7F

    @property
    def default_length(self) -> int:
        """Get/set the default note length (6 = 1/16)."""
        data = self._part._bank._bank_file._data
        return data[self._values_offset() + MidiTrackValuesOffset.LENGTH]

    @default_length.setter
    def default_length(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._values_offset() + MidiTrackValuesOffset.LENGTH] = value & 0xFF

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
        data = self._part._bank._bank_file._data
        offset = self._setup_offset() + 19 + n  # CC1 is at offset 20
        return data[offset]

    def set_cc_number(self, n: int, value: int):
        """
        Set the MIDI CC number assigned to slot n (1-10).

        Args:
            n: CC slot number (1-10)
            value: MIDI CC number (0-127)
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        data = self._part._bank._bank_file._data
        offset = self._setup_offset() + 19 + n  # CC1 is at offset 20
        data[offset] = value & 0x7F

    # === CC Default Values ===

    @property
    def pitch_bend(self) -> int:
        """Get/set default pitch bend (0-127, 64 = center)."""
        data = self._part._bank._bank_file._data
        return data[self._values_offset() + MidiTrackValuesOffset.PITCH_BEND]

    @pitch_bend.setter
    def pitch_bend(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._values_offset() + MidiTrackValuesOffset.PITCH_BEND] = value & 0x7F

    @property
    def aftertouch(self) -> int:
        """Get/set default aftertouch (0-127)."""
        data = self._part._bank._bank_file._data
        return data[self._values_offset() + MidiTrackValuesOffset.AFTERTOUCH]

    @aftertouch.setter
    def aftertouch(self, value: int):
        data = self._part._bank._bank_file._data
        data[self._values_offset() + MidiTrackValuesOffset.AFTERTOUCH] = value & 0x7F

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
        data = self._part._bank._bank_file._data
        offset = self._values_offset() + 19 + n  # CC1 is at offset 20
        return data[offset]

    def set_cc_value(self, n: int, value: int):
        """
        Set the default value for CC slot n (1-10).

        Args:
            n: CC slot number (1-10)
            value: Default CC value (0-127)
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        data = self._part._bank._bank_file._data
        offset = self._values_offset() + 19 + n  # CC1 is at offset 20
        data[offset] = value & 0x7F


class Part:
    """
    Pythonic interface for an Octatrack Part.

    A Part holds machine configurations for all 8 tracks.
    Each bank has 4 parts.

    Usage:
        part = bank.part(1)
        track = part.track(1)
        track.machine_type = MachineType.FLEX
    """

    def __init__(self, bank: "Bank", part_num: int):
        self._bank = bank
        self._part_num = part_num
        self._tracks: Dict[int, AudioPartTrack] = {}
        self._midi_tracks: Dict[int, MidiPartTrack] = {}

    def _part_offset(self) -> int:
        """Get the byte offset for this part in the bank file."""
        return self._bank._bank_file.part_offset(self._part_num)

    def track(self, track_num: int) -> AudioPartTrack:
        """
        Get a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioPartTrack instance for configuring machine settings
        """
        if track_num not in self._tracks:
            self._tracks[track_num] = AudioPartTrack(self, track_num)
        return self._tracks[track_num]

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
