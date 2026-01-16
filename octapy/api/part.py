"""
Part and PartTrack classes for sound configuration.
"""

from typing import TYPE_CHECKING, Dict

from .._io import PartOffset, MachineSlotOffset, MACHINE_SLOT_SIZE
from .base import MachineType

if TYPE_CHECKING:
    from .bank import Bank


class PartTrack:
    """
    Sound configuration for a track within a Part.

    Provides access to machine type, sample slots, and track settings.
    This is separate from PatternTrack which handles sequencing.

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
        self._tracks: Dict[int, PartTrack] = {}

    def _part_offset(self) -> int:
        """Get the byte offset for this part in the bank file."""
        return self._bank._bank_file.part_offset(self._part_num)

    def track(self, track_num: int) -> PartTrack:
        """
        Get a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            PartTrack instance for configuring machine settings
        """
        if track_num not in self._tracks:
            self._tracks[track_num] = PartTrack(self, track_num)
        return self._tracks[track_num]

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
