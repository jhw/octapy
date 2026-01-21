"""
MidiPartTrack - standalone MIDI track configuration data for a Part.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Part binary data.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional

from ...._io import (
    MidiPartOffset,
    MidiTrackValuesOffset,
    MidiTrackSetupOffset,
    MIDI_TRACK_VALUES_SIZE,
    MIDI_TRACK_SETUP_SIZE,
)
from ...utils import quantize_note_length


# Combined size: values (32) + setup (36) = 68 bytes
MIDI_PART_TRACK_SIZE = MIDI_TRACK_VALUES_SIZE + MIDI_TRACK_SETUP_SIZE


class TrackDataOffset(IntEnum):
    """Offsets within standalone MidiPartTrack buffer (68 bytes).

    The standalone buffer is contiguous:
    - bytes 0-31: MidiTrackParamsValues (from Part)
    - bytes 32-67: MidiTrackParamsSetup (from Part)
    """
    # Values section (0-31)
    NOTE = 0
    VELOCITY = 1
    LENGTH = 2
    NOTE2 = 3
    NOTE3 = 4
    NOTE4 = 5
    LFO_SPD1 = 6
    LFO_SPD2 = 7
    LFO_SPD3 = 8
    LFO_DEP1 = 9
    LFO_DEP2 = 10
    LFO_DEP3 = 11
    ARP_TRAN = 12
    ARP_LEG = 13
    ARP_MODE = 14
    ARP_SPD = 15
    ARP_RNGE = 16
    ARP_NLEN = 17
    PITCH_BEND = 18
    AFTERTOUCH = 19
    CC1_VALUE = 20
    CC2_VALUE = 21
    CC3_VALUE = 22
    CC4_VALUE = 23
    CC5_VALUE = 24
    CC6_VALUE = 25
    CC7_VALUE = 26
    CC8_VALUE = 27
    CC9_VALUE = 28
    CC10_VALUE = 29

    # Setup section (32-67)
    CHANNEL = 32
    BANK = 33
    PROGRAM = 34
    SBANK = 36
    LFO1_PMTR = 38
    LFO2_PMTR = 39
    LFO3_PMTR = 40
    LFO1_WAVE = 41
    LFO2_WAVE = 42
    LFO3_WAVE = 43
    ARP_LEN = 46
    ARP_KEY = 49
    CC1_NUMBER = 52
    CC2_NUMBER = 53
    CC3_NUMBER = 54
    CC4_NUMBER = 55
    CC5_NUMBER = 56
    CC6_NUMBER = 57
    CC7_NUMBER = 58
    CC8_NUMBER = 59
    CC9_NUMBER = 60
    CC10_NUMBER = 61
    LFO1_MULT = 62
    LFO2_MULT = 63
    LFO3_MULT = 64
    LFO1_TRIG = 65
    LFO2_TRIG = 66
    LFO3_TRIG = 67


class MidiPartTrack:
    """
    MIDI track configuration for a Part.

    This is a standalone object that can be created with constructor arguments
    or read from Part binary data. It owns its data buffer.

    NOTE Page Encoders:
        A: NOTE (note)            - default_note property
        B: VEL (velocity)         - default_velocity property
        C: LEN (length)           - default_length property
        D: NOT2 (note 2)          - default_note2 property (chord)
        E: NOT3 (note 3)          - default_note3 property (chord)
        F: NOT4 (note 4)          - default_note4 property (chord)

    Usage:
        # Create with constructor arguments
        track = MidiPartTrack(
            track_num=1,
            channel=5,
            default_note=60,
            default_velocity=100,
        )

        # Read from Part binary (called by Part)
        track = MidiPartTrack.read_from_part(track_num, part_data, part_offset)

        # Write to binary
        data = track.write()
    """

    def __init__(
        self,
        track_num: int = 1,
        channel: Optional[int] = None,
        bank: Optional[int] = None,
        program: Optional[int] = None,
        default_note: Optional[int] = None,
        default_velocity: Optional[int] = None,
        default_length: Optional[int] = None,
        default_note2: Optional[int] = None,
        default_note3: Optional[int] = None,
        default_note4: Optional[int] = None,
        pitch_bend: Optional[int] = None,
        aftertouch: Optional[int] = None,
        arp_transpose: Optional[int] = None,
        arp_legato: Optional[int] = None,
        arp_mode: Optional[int] = None,
        arp_speed: Optional[int] = None,
        arp_range: Optional[int] = None,
        arp_note_length: Optional[int] = None,
    ):
        """
        Create a MidiPartTrack with optional parameter overrides.

        Args:
            track_num: Track number (1-8)
            channel: MIDI channel (0-15)
            bank: Bank select (0-127, 128=off)
            program: Program change (0-127, 128=off)
            default_note: Default note (0-127, 60=Middle C)
            default_velocity: Default velocity (0-127)
            default_length: Default note length (quantized)
            default_note2: Default note 2 for chords (0-127, 64=off)
            default_note3: Default note 3 for chords (0-127, 64=off)
            default_note4: Default note 4 for chords (0-127, 64=off)
            pitch_bend: Default pitch bend (0-127, 64=center)
            aftertouch: Default aftertouch (0-127)
            arp_transpose: Arp transpose (0-127, 64=no transpose)
            arp_legato: Arp legato (0-127)
            arp_mode: Arp mode (0-127)
            arp_speed: Arp speed (0-127)
            arp_range: Arp range (0-127)
            arp_note_length: Arp note length (quantized)
        """
        self._track_num = track_num
        self._data = bytearray(MIDI_PART_TRACK_SIZE)

        # Initialize with sensible defaults
        # Channel defaults to track_num - 1 (track 1 -> channel 0)
        self._data[TrackDataOffset.CHANNEL] = (track_num - 1) & 0x0F
        self._data[TrackDataOffset.BANK] = 128  # Off
        self._data[TrackDataOffset.PROGRAM] = 128  # Off
        self._data[TrackDataOffset.NOTE] = 48  # C3
        self._data[TrackDataOffset.VELOCITY] = 100
        self._data[TrackDataOffset.LENGTH] = 6  # 1/16 note
        self._data[TrackDataOffset.NOTE2] = 64  # No chord offset
        self._data[TrackDataOffset.NOTE3] = 64
        self._data[TrackDataOffset.NOTE4] = 64
        self._data[TrackDataOffset.PITCH_BEND] = 64  # Center
        self._data[TrackDataOffset.AFTERTOUCH] = 0
        self._data[TrackDataOffset.ARP_TRAN] = 64  # No transpose
        self._data[TrackDataOffset.ARP_LEG] = 0
        self._data[TrackDataOffset.ARP_MODE] = 0
        self._data[TrackDataOffset.ARP_SPD] = 12
        self._data[TrackDataOffset.ARP_RNGE] = 0
        self._data[TrackDataOffset.ARP_NLEN] = 6

        # Apply overrides
        if channel is not None:
            self.channel = channel
        if bank is not None:
            self.bank = bank
        if program is not None:
            self.program = program
        if default_note is not None:
            self.default_note = default_note
        if default_velocity is not None:
            self.default_velocity = default_velocity
        if default_length is not None:
            self.default_length = default_length
        if default_note2 is not None:
            self.default_note2 = default_note2
        if default_note3 is not None:
            self.default_note3 = default_note3
        if default_note4 is not None:
            self.default_note4 = default_note4
        if pitch_bend is not None:
            self.pitch_bend = pitch_bend
        if aftertouch is not None:
            self.aftertouch = aftertouch
        if arp_transpose is not None:
            self.arp_transpose = arp_transpose
        if arp_legato is not None:
            self.arp_legato = arp_legato
        if arp_mode is not None:
            self.arp_mode = arp_mode
        if arp_speed is not None:
            self.arp_speed = arp_speed
        if arp_range is not None:
            self.arp_range = arp_range
        if arp_note_length is not None:
            self.arp_note_length = arp_note_length

    @classmethod
    def read_from_part(cls, track_num: int, part_data: bytes, part_offset: int = 0) -> "MidiPartTrack":
        """
        Read a MidiPartTrack from Part binary data.

        The MIDI track data is scattered in the Part:
        - MidiTrackParamsValues at MidiPartOffset.MIDI_TRACK_PARAMS_VALUES
        - MidiTrackParamsSetup at MidiPartOffset.MIDI_TRACK_PARAMS_SETUP

        Args:
            track_num: Track number (1-8)
            part_data: Part binary data
            part_offset: Offset to Part data in part_data buffer

        Returns:
            MidiPartTrack instance
        """
        instance = cls.__new__(cls)
        instance._track_num = track_num
        instance._data = bytearray(MIDI_PART_TRACK_SIZE)

        track_idx = track_num - 1

        # Read values section
        values_offset = part_offset + MidiPartOffset.MIDI_TRACK_PARAMS_VALUES + track_idx * MIDI_TRACK_VALUES_SIZE
        instance._data[0:MIDI_TRACK_VALUES_SIZE] = part_data[values_offset:values_offset + MIDI_TRACK_VALUES_SIZE]

        # Read setup section
        setup_offset = part_offset + MidiPartOffset.MIDI_TRACK_PARAMS_SETUP + track_idx * MIDI_TRACK_SETUP_SIZE
        instance._data[MIDI_TRACK_VALUES_SIZE:MIDI_PART_TRACK_SIZE] = part_data[setup_offset:setup_offset + MIDI_TRACK_SETUP_SIZE]

        return instance

    def write(self) -> bytes:
        """
        Write this MidiPartTrack to binary data.

        Returns the contiguous buffer. Use write_to_part() to write back
        to a Part's scattered layout.

        Returns:
            MIDI_PART_TRACK_SIZE bytes
        """
        return bytes(self._data)

    def write_to_part(self, part_data: bytearray, part_offset: int = 0):
        """
        Write this MidiPartTrack back to Part binary data.

        Writes to the scattered locations in the Part.

        Args:
            part_data: Part binary data (modified in place)
            part_offset: Offset to Part data in part_data buffer
        """
        track_idx = self._track_num - 1

        # Write values section
        values_offset = part_offset + MidiPartOffset.MIDI_TRACK_PARAMS_VALUES + track_idx * MIDI_TRACK_VALUES_SIZE
        part_data[values_offset:values_offset + MIDI_TRACK_VALUES_SIZE] = self._data[0:MIDI_TRACK_VALUES_SIZE]

        # Write setup section
        setup_offset = part_offset + MidiPartOffset.MIDI_TRACK_PARAMS_SETUP + track_idx * MIDI_TRACK_SETUP_SIZE
        part_data[setup_offset:setup_offset + MIDI_TRACK_SETUP_SIZE] = self._data[MIDI_TRACK_VALUES_SIZE:MIDI_PART_TRACK_SIZE]

    def clone(self) -> "MidiPartTrack":
        """Create a copy of this MidiPartTrack."""
        instance = MidiPartTrack.__new__(MidiPartTrack)
        instance._track_num = self._track_num
        instance._data = bytearray(self._data)
        return instance

    # === Basic properties ===

    @property
    def track_num(self) -> int:
        """Get the track number (1-8)."""
        return self._track_num

    # === Setup properties ===

    @property
    def channel(self) -> int:
        """Get/set the MIDI channel (0-15)."""
        return self._data[TrackDataOffset.CHANNEL]

    @channel.setter
    def channel(self, value: int):
        self._data[TrackDataOffset.CHANNEL] = value & 0x0F

    @property
    def bank(self) -> int:
        """Get/set the bank select (128 = off)."""
        return self._data[TrackDataOffset.BANK]

    @bank.setter
    def bank(self, value: int):
        self._data[TrackDataOffset.BANK] = value & 0xFF

    @property
    def program(self) -> int:
        """Get/set the program change (128 = off)."""
        return self._data[TrackDataOffset.PROGRAM]

    @program.setter
    def program(self, value: int):
        self._data[TrackDataOffset.PROGRAM] = value & 0xFF

    # === NOTE Page (Values) ===

    @property
    def default_note(self) -> int:
        """Get/set the default note (0-127, 60=Middle C)."""
        return self._data[TrackDataOffset.NOTE]

    @default_note.setter
    def default_note(self, value: int):
        self._data[TrackDataOffset.NOTE] = value & 0x7F

    @property
    def default_velocity(self) -> int:
        """Get/set the default velocity (0-127)."""
        return self._data[TrackDataOffset.VELOCITY]

    @default_velocity.setter
    def default_velocity(self, value: int):
        self._data[TrackDataOffset.VELOCITY] = value & 0x7F

    @property
    def default_length(self) -> int:
        """Get/set the default note length (quantized to valid values)."""
        raw = self._data[TrackDataOffset.LENGTH]
        return quantize_note_length(raw)

    @default_length.setter
    def default_length(self, value: int):
        self._data[TrackDataOffset.LENGTH] = quantize_note_length(value)

    @property
    def default_note2(self) -> int:
        """Get/set the default note 2 for chords (0-127, 64 = no offset)."""
        return self._data[TrackDataOffset.NOTE2]

    @default_note2.setter
    def default_note2(self, value: int):
        self._data[TrackDataOffset.NOTE2] = value & 0x7F

    @property
    def default_note3(self) -> int:
        """Get/set the default note 3 for chords (0-127, 64 = no offset)."""
        return self._data[TrackDataOffset.NOTE3]

    @default_note3.setter
    def default_note3(self, value: int):
        self._data[TrackDataOffset.NOTE3] = value & 0x7F

    @property
    def default_note4(self) -> int:
        """Get/set the default note 4 for chords (0-127, 64 = no offset)."""
        return self._data[TrackDataOffset.NOTE4]

    @default_note4.setter
    def default_note4(self, value: int):
        self._data[TrackDataOffset.NOTE4] = value & 0x7F

    # === CC Values ===

    @property
    def pitch_bend(self) -> int:
        """Get/set default pitch bend (0-127, 64 = center)."""
        return self._data[TrackDataOffset.PITCH_BEND]

    @pitch_bend.setter
    def pitch_bend(self, value: int):
        self._data[TrackDataOffset.PITCH_BEND] = value & 0x7F

    @property
    def aftertouch(self) -> int:
        """Get/set default aftertouch (0-127)."""
        return self._data[TrackDataOffset.AFTERTOUCH]

    @aftertouch.setter
    def aftertouch(self, value: int):
        self._data[TrackDataOffset.AFTERTOUCH] = value & 0x7F

    def cc_value(self, n: int) -> int:
        """Get default value for CC slot n (1-10)."""
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = TrackDataOffset.CC1_VALUE + (n - 1)
        return self._data[offset]

    def set_cc_value(self, n: int, value: int):
        """Set default value for CC slot n (1-10)."""
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = TrackDataOffset.CC1_VALUE + (n - 1)
        self._data[offset] = value & 0x7F

    # === CC Number Assignments ===

    def cc_number(self, n: int) -> int:
        """Get MIDI CC number assigned to slot n (1-10)."""
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = TrackDataOffset.CC1_NUMBER + (n - 1)
        return self._data[offset]

    def set_cc_number(self, n: int, value: int):
        """Set MIDI CC number assigned to slot n (1-10)."""
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        offset = TrackDataOffset.CC1_NUMBER + (n - 1)
        self._data[offset] = value & 0x7F

    # === ARP Page ===

    @property
    def arp_transpose(self) -> int:
        """Get/set arpeggiator transpose (0-127, 64 = no transpose)."""
        return self._data[TrackDataOffset.ARP_TRAN]

    @arp_transpose.setter
    def arp_transpose(self, value: int):
        self._data[TrackDataOffset.ARP_TRAN] = value & 0x7F

    @property
    def arp_legato(self) -> int:
        """Get/set arpeggiator legato (0-127)."""
        return self._data[TrackDataOffset.ARP_LEG]

    @arp_legato.setter
    def arp_legato(self, value: int):
        self._data[TrackDataOffset.ARP_LEG] = value & 0x7F

    @property
    def arp_mode(self) -> int:
        """Get/set arpeggiator mode (0-127)."""
        return self._data[TrackDataOffset.ARP_MODE]

    @arp_mode.setter
    def arp_mode(self, value: int):
        self._data[TrackDataOffset.ARP_MODE] = value & 0x7F

    @property
    def arp_speed(self) -> int:
        """Get/set arpeggiator speed (0-127)."""
        return self._data[TrackDataOffset.ARP_SPD]

    @arp_speed.setter
    def arp_speed(self, value: int):
        self._data[TrackDataOffset.ARP_SPD] = value & 0x7F

    @property
    def arp_range(self) -> int:
        """Get/set arpeggiator range (0-127)."""
        return self._data[TrackDataOffset.ARP_RNGE]

    @arp_range.setter
    def arp_range(self, value: int):
        self._data[TrackDataOffset.ARP_RNGE] = value & 0x7F

    @property
    def arp_note_length(self) -> int:
        """Get/set arpeggiator note length (quantized)."""
        raw = self._data[TrackDataOffset.ARP_NLEN]
        return quantize_note_length(raw)

    @arp_note_length.setter
    def arp_note_length(self, value: int):
        self._data[TrackDataOffset.ARP_NLEN] = quantize_note_length(value)

    # === Serialization ===

    def to_dict(self) -> dict:
        """
        Convert MIDI part track to dictionary.

        Returns dict with MIDI channel, program, note defaults, and arp settings.
        """
        cc_numbers = {n: self.cc_number(n) for n in range(1, 11)}
        cc_values = {n: self.cc_value(n) for n in range(1, 11)}

        return {
            "track": self._track_num,
            "channel": self.channel,
            "bank": self.bank,
            "program": self.program,
            "note": {
                "default_note": self.default_note,
                "default_velocity": self.default_velocity,
                "default_length": self.default_length,
                "default_note2": self.default_note2,
                "default_note3": self.default_note3,
                "default_note4": self.default_note4,
            },
            "cc": {
                "pitch_bend": self.pitch_bend,
                "aftertouch": self.aftertouch,
                "numbers": cc_numbers,
                "values": cc_values,
            },
            "arp": {
                "transpose": self.arp_transpose,
                "legato": self.arp_legato,
                "mode": self.arp_mode,
                "speed": self.arp_speed,
                "range": self.arp_range,
                "note_length": self.arp_note_length,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MidiPartTrack":
        """Create a MidiPartTrack from a dictionary."""
        track = cls(track_num=data.get("track", 1))

        if "channel" in data:
            track.channel = data["channel"]
        if "bank" in data:
            track.bank = data["bank"]
        if "program" in data:
            track.program = data["program"]

        if "note" in data:
            note = data["note"]
            if "default_note" in note:
                track.default_note = note["default_note"]
            if "default_velocity" in note:
                track.default_velocity = note["default_velocity"]
            if "default_length" in note:
                track.default_length = note["default_length"]
            if "default_note2" in note:
                track.default_note2 = note["default_note2"]
            if "default_note3" in note:
                track.default_note3 = note["default_note3"]
            if "default_note4" in note:
                track.default_note4 = note["default_note4"]

        if "cc" in data:
            cc = data["cc"]
            if "pitch_bend" in cc:
                track.pitch_bend = cc["pitch_bend"]
            if "aftertouch" in cc:
                track.aftertouch = cc["aftertouch"]
            if "numbers" in cc:
                for n, val in cc["numbers"].items():
                    track.set_cc_number(int(n), val)
            if "values" in cc:
                for n, val in cc["values"].items():
                    track.set_cc_value(int(n), val)

        if "arp" in data:
            arp = data["arp"]
            if "transpose" in arp:
                track.arp_transpose = arp["transpose"]
            if "legato" in arp:
                track.arp_legato = arp["legato"]
            if "mode" in arp:
                track.arp_mode = arp["mode"]
            if "speed" in arp:
                track.arp_speed = arp["speed"]
            if "range" in arp:
                track.arp_range = arp["range"]
            if "note_length" in arp:
                track.arp_note_length = arp["note_length"]

        return track

    def __eq__(self, other) -> bool:
        """Check equality based on data buffer."""
        if not isinstance(other, MidiPartTrack):
            return NotImplemented
        return self._track_num == other._track_num and self._data == other._data

    def __repr__(self) -> str:
        return f"MidiPartTrack(track={self._track_num}, channel={self.channel})"
