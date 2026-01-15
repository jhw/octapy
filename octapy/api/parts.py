"""
Part data structures for Octatrack banks.

A Part contains track settings for 8 audio and 8 MIDI tracks:
- Machine types and slot assignments
- Parameter values (amp, fx, lfo)
- Recorder setup
- Scenes

Each bank has 4 parts (ONE, TWO, THREE, FOUR), stored twice:
- Unsaved state (working copy)
- Saved state (last explicitly saved)

Ported from ot-tools-io (Rust).
"""

from enum import IntEnum
from typing import List

from . import OTBlock, MachineType, _read_fixed_string, _write_fixed_string


# Part block size (calculated from Rust struct layout)
# header(4) + data_block_1(4) + part_id(1) + fx1(8) + fx2(8) + scenes(2) +
# volumes(16) + machine_types(8) + machine_params(240) + params_values(192) +
# machine_setup(240) + machine_slots(40) + params_setup(288) +
# midi_params_values(272) + midi_params_setup(288) + recorder_setup(96) +
# scene_params(4352) + scene_xlvs(160) + custom_lfos_audio(128) +
# custom_lfo_interp_audio(16) + custom_lfos_midi(128) + custom_lfo_interp_midi(16) +
# arp_mutes(16) + arp_seqs(128) = ~6626 bytes per part (approximate)
PART_BLOCK_SIZE = 6626  # Approximate - actual size determined by template

PART_HEADER = bytes([0x50, 0x41, 0x52, 0x54])  # "PART"


class PartOffset(IntEnum):
    """Byte offsets within a Part block."""
    HEADER = 0                      # 4 bytes: "PART"
    DATA_BLOCK_1 = 4                # 4 bytes: always 0
    PART_ID = 8                     # 1 byte: 0-3
    AUDIO_TRACK_FX1 = 9             # 8 bytes: FX1 type per track
    AUDIO_TRACK_FX2 = 17            # 8 bytes: FX2 type per track
    ACTIVE_SCENE_A = 25             # 1 byte: scene A (0-15)
    ACTIVE_SCENE_B = 26             # 1 byte: scene B (0-15)
    AUDIO_TRACK_VOLUMES = 27        # 16 bytes: main/cue volume per track (2 each)
    AUDIO_TRACK_MACHINE_TYPES = 43  # 8 bytes: machine type per track
    # Offset 51: machine_params (240 bytes = 8 tracks * 30 bytes)
    # Offset 291: params_values (192 bytes = 8 tracks * 24 bytes)
    # Offset 483: machine_setup (240 bytes = 8 tracks * 30 bytes)
    AUDIO_TRACK_MACHINE_SLOTS = 723 # 40 bytes: 8 tracks * 5 bytes (slot assignments)


# Machine slot offsets (relative to slot array start)
class MachineSlotOffset(IntEnum):
    """Offsets within AudioTrackMachineSlot (5 bytes per track)."""
    STATIC_SLOT_ID = 0
    FLEX_SLOT_ID = 1
    UNUSED_1 = 2
    UNUSED_2 = 3
    RECORDER_SLOT_ID = 4


# Size of machine slot struct
MACHINE_SLOT_SIZE = 5


class Part(OTBlock):
    """
    An Octatrack Part containing track settings.

    Parts store machine types, slot assignments, and all parameter values
    for the 8 audio and 8 MIDI tracks.
    """

    BLOCK_SIZE = PART_BLOCK_SIZE

    def __init__(self, part_id: int = 0):
        super().__init__()
        self._data = bytearray(PART_BLOCK_SIZE)

        # Set header
        self._data[0:4] = PART_HEADER

        # Set part ID
        self._data[PartOffset.PART_ID] = part_id

        # Set default FX (Filter for FX1, Delay for FX2)
        for i in range(8):
            self._data[PartOffset.AUDIO_TRACK_FX1 + i] = 4  # Filter
            self._data[PartOffset.AUDIO_TRACK_FX2 + i] = 8  # Delay

        # Set default scenes (A=0, B=8)
        self._data[PartOffset.ACTIVE_SCENE_A] = 0
        self._data[PartOffset.ACTIVE_SCENE_B] = 8

        # Set default volumes (108 for both main and cue)
        for i in range(8):
            self._data[PartOffset.AUDIO_TRACK_VOLUMES + i * 2] = 108
            self._data[PartOffset.AUDIO_TRACK_VOLUMES + i * 2 + 1] = 108

        # Set default machine types (all Static)
        for i in range(8):
            self._data[PartOffset.AUDIO_TRACK_MACHINE_TYPES + i] = MachineType.STATIC

    @property
    def part_id(self) -> int:
        """Get the part ID (0-3)."""
        return self._data[PartOffset.PART_ID]

    @part_id.setter
    def part_id(self, value: int):
        """Set the part ID (0-3)."""
        self._data[PartOffset.PART_ID] = value & 0x03

    def get_machine_type(self, track: int) -> MachineType:
        """
        Get the machine type for an audio track.

        Args:
            track: Track number (1-8)

        Returns:
            MachineType enum value
        """
        offset = PartOffset.AUDIO_TRACK_MACHINE_TYPES + (track - 1)
        return MachineType(self._data[offset])

    def set_machine_type(self, track: int, machine_type: MachineType):
        """
        Set the machine type for an audio track.

        Args:
            track: Track number (1-8)
            machine_type: MachineType enum value
        """
        offset = PartOffset.AUDIO_TRACK_MACHINE_TYPES + (track - 1)
        self._data[offset] = machine_type

    def get_volume(self, track: int) -> tuple:
        """
        Get main and cue volume for a track.

        Args:
            track: Track number (1-8)

        Returns:
            Tuple of (main_volume, cue_volume)
        """
        offset = PartOffset.AUDIO_TRACK_VOLUMES + (track - 1) * 2
        return (self._data[offset], self._data[offset + 1])

    def set_volume(self, track: int, main: int = 108, cue: int = 108):
        """
        Set main and cue volume for a track.

        Args:
            track: Track number (1-8)
            main: Main volume (0-127, default 108)
            cue: Cue volume (0-127, default 108)
        """
        offset = PartOffset.AUDIO_TRACK_VOLUMES + (track - 1) * 2
        self._data[offset] = main & 0x7F
        self._data[offset + 1] = cue & 0x7F

    def get_fx1_type(self, track: int) -> int:
        """Get FX1 type for a track."""
        return self._data[PartOffset.AUDIO_TRACK_FX1 + (track - 1)]

    def set_fx1_type(self, track: int, fx_type: int):
        """Set FX1 type for a track."""
        self._data[PartOffset.AUDIO_TRACK_FX1 + (track - 1)] = fx_type

    def get_fx2_type(self, track: int) -> int:
        """Get FX2 type for a track."""
        return self._data[PartOffset.AUDIO_TRACK_FX2 + (track - 1)]

    def set_fx2_type(self, track: int, fx_type: int):
        """Set FX2 type for a track."""
        self._data[PartOffset.AUDIO_TRACK_FX2 + (track - 1)] = fx_type

    @property
    def active_scene_a(self) -> int:
        """Get active scene A (0-15)."""
        return self._data[PartOffset.ACTIVE_SCENE_A]

    @active_scene_a.setter
    def active_scene_a(self, value: int):
        """Set active scene A (0-15)."""
        self._data[PartOffset.ACTIVE_SCENE_A] = value & 0x0F

    @property
    def active_scene_b(self) -> int:
        """Get active scene B (0-15)."""
        return self._data[PartOffset.ACTIVE_SCENE_B]

    @active_scene_b.setter
    def active_scene_b(self, value: int):
        """Set active scene B (0-15)."""
        self._data[PartOffset.ACTIVE_SCENE_B] = value & 0x0F

    def check_header(self) -> bool:
        """Verify the header matches expected Part header."""
        return bytes(self._data[0:4]) == PART_HEADER

    # === Slot assignments ===

    def get_flex_slot(self, track: int) -> int:
        """
        Get the flex sample slot assigned to a track.

        Args:
            track: Track number (1-8)

        Returns:
            Slot number (0-indexed, 0-127 for samples, 128-135 for recorders)
        """
        slot_offset = PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (track - 1) * MACHINE_SLOT_SIZE
        return self._data[slot_offset + MachineSlotOffset.FLEX_SLOT_ID]

    def set_flex_slot(self, track: int, slot: int):
        """
        Set the flex sample slot for a track.

        Args:
            track: Track number (1-8)
            slot: Slot number (0-indexed, 0-127 for samples, 128-135 for recorders)
        """
        slot_offset = PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (track - 1) * MACHINE_SLOT_SIZE
        self._data[slot_offset + MachineSlotOffset.FLEX_SLOT_ID] = slot & 0xFF

    def get_static_slot(self, track: int) -> int:
        """
        Get the static sample slot assigned to a track.

        Args:
            track: Track number (1-8)

        Returns:
            Slot number (0-indexed, 0-127)
        """
        slot_offset = PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (track - 1) * MACHINE_SLOT_SIZE
        return self._data[slot_offset + MachineSlotOffset.STATIC_SLOT_ID]

    def set_static_slot(self, track: int, slot: int):
        """
        Set the static sample slot for a track.

        Args:
            track: Track number (1-8)
            slot: Slot number (0-indexed, 0-127)
        """
        slot_offset = PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (track - 1) * MACHINE_SLOT_SIZE
        self._data[slot_offset + MachineSlotOffset.STATIC_SLOT_ID] = slot & 0xFF

    def get_recorder_slot(self, track: int) -> int:
        """
        Get the recorder buffer slot assigned to a track.

        Args:
            track: Track number (1-8)

        Returns:
            Slot number (128-135 for recorder buffers)
        """
        slot_offset = PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (track - 1) * MACHINE_SLOT_SIZE
        return self._data[slot_offset + MachineSlotOffset.RECORDER_SLOT_ID]

    def set_recorder_slot(self, track: int, slot: int):
        """
        Set the recorder buffer slot for a track.

        Args:
            track: Track number (1-8)
            slot: Slot number (128-135 for recorder buffers)
        """
        slot_offset = PartOffset.AUDIO_TRACK_MACHINE_SLOTS + (track - 1) * MACHINE_SLOT_SIZE
        self._data[slot_offset + MachineSlotOffset.RECORDER_SLOT_ID] = slot & 0xFF


class Parts:
    """
    Container for the 4 unsaved and 4 saved parts in a bank.

    The Octatrack maintains two copies of each part:
    - unsaved: Current working state
    - saved: Last explicitly saved state (via Part menu)
    """

    def __init__(self):
        self.unsaved: List[Part] = [Part(i) for i in range(4)]
        self.saved: List[Part] = [Part(i) for i in range(4)]

    @classmethod
    def read(cls, data, unsaved_offset: int, saved_offset: int, part_size: int):
        """
        Read parts from binary data.

        Args:
            data: Full bank data buffer
            unsaved_offset: Offset to unsaved parts array
            saved_offset: Offset to saved parts array
            part_size: Size of each Part block

        Returns:
            Parts instance
        """
        instance = cls.__new__(cls)
        instance.unsaved = []
        instance.saved = []

        for i in range(4):
            # Read unsaved part
            start = unsaved_offset + i * part_size
            part_data = data[start:start + part_size]
            part = Part.__new__(Part)
            part._data = bytearray(part_data)
            instance.unsaved.append(part)

            # Read saved part
            start = saved_offset + i * part_size
            part_data = data[start:start + part_size]
            part = Part.__new__(Part)
            part._data = bytearray(part_data)
            instance.saved.append(part)

        return instance

    def write_to(self, data, unsaved_offset: int, saved_offset: int):
        """
        Write parts back to binary data buffer.

        Args:
            data: Full bank data buffer (modified in place)
            unsaved_offset: Offset to unsaved parts array
            saved_offset: Offset to saved parts array
        """
        for i, part in enumerate(self.unsaved):
            start = unsaved_offset + i * len(part._data)
            data[start:start + len(part._data)] = part._data

        for i, part in enumerate(self.saved):
            start = saved_offset + i * len(part._data)
            data[start:start + len(part._data)] = part._data
