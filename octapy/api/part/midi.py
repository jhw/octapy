"""
MidiPartTrack - MIDI track configuration.
"""

from __future__ import annotations

from ..._io import (
    MidiPartOffset,
    MidiTrackValuesOffset,
    MidiTrackSetupOffset,
    MIDI_TRACK_VALUES_SIZE,
    MIDI_TRACK_SETUP_SIZE,
)
from ..utils import quantize_note_length
from .base import BasePartTrack


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
        from octapy.api.enums import MidiNote

        midi_track = part.midi_track(1)
        midi_track.channel = 5                    # MIDI channel 6 (0-indexed)
        midi_track.program = 32                   # Program 33
        midi_track.default_note = MidiNote.C4    # Middle C (60)
        midi_track.default_note = MidiNote.A4    # Concert pitch A (69)
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

    # === NOTE Page (Values) ===

    @property
    def default_note(self) -> int:
        """
        Get/set the default note (0-127).

        Accepts MidiNote enum values or raw integers.
        Standard MIDI mapping: C-1 = 0, C4 = 60 (Middle C), G9 = 127.
        Default is 48 (C3).
        """
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
        """
        Get/set the default note length.

        Values are quantized to valid NoteLength values:
        3 (1/32), 6 (1/16), 12 (1/8), 24 (1/4), 48 (1/2)
        """
        raw = self._data[self._values_offset() + MidiTrackValuesOffset.LENGTH]
        return quantize_note_length(raw)

    @default_length.setter
    def default_length(self, value: int):
        quantized = quantize_note_length(value)
        self._data[self._values_offset() + MidiTrackValuesOffset.LENGTH] = quantized

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

    # === ARP Page ===
    #
    # ARP Page Encoders:
    #     A: TRAN (transpose)   - arp_transpose property
    #     B: LEG (legato)       - arp_legato property
    #     C: MODE (arp mode)    - arp_mode property
    #     D: SPD (speed)        - arp_speed property
    #     E: RNGE (range)       - arp_range property
    #     F: NLEN (note length) - arp_note_length property

    @property
    def arp_transpose(self) -> int:
        """Get/set arpeggiator transpose (0-127, 64 = no transpose)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.ARP_TRAN]

    @arp_transpose.setter
    def arp_transpose(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.ARP_TRAN] = value & 0x7F

    @property
    def arp_legato(self) -> int:
        """Get/set arpeggiator legato (0-127)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.ARP_LEG]

    @arp_legato.setter
    def arp_legato(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.ARP_LEG] = value & 0x7F

    @property
    def arp_mode(self) -> int:
        """Get/set arpeggiator mode (0-127)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.ARP_MODE]

    @arp_mode.setter
    def arp_mode(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.ARP_MODE] = value & 0x7F

    @property
    def arp_speed(self) -> int:
        """Get/set arpeggiator speed (0-127)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.ARP_SPD]

    @arp_speed.setter
    def arp_speed(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.ARP_SPD] = value & 0x7F

    @property
    def arp_range(self) -> int:
        """Get/set arpeggiator range (0-127)."""
        return self._data[self._values_offset() + MidiTrackValuesOffset.ARP_RNGE]

    @arp_range.setter
    def arp_range(self, value: int):
        self._data[self._values_offset() + MidiTrackValuesOffset.ARP_RNGE] = value & 0x7F

    @property
    def arp_note_length(self) -> int:
        """
        Get/set arpeggiator note length.

        Values are quantized to valid NoteLength values:
        3 (1/32), 6 (1/16), 12 (1/8), 24 (1/4), 48 (1/2)
        """
        raw = self._data[self._values_offset() + MidiTrackValuesOffset.ARP_NLEN]
        return quantize_note_length(raw)

    @arp_note_length.setter
    def arp_note_length(self, value: int):
        quantized = quantize_note_length(value)
        self._data[self._values_offset() + MidiTrackValuesOffset.ARP_NLEN] = quantized

    def to_dict(self) -> dict:
        """
        Convert MIDI part track to dictionary.

        Returns dict with MIDI channel, program, note defaults, and arp settings.
        """
        # Collect CC numbers and values
        cc_numbers = {}
        cc_values = {}
        for n in range(1, 11):
            cc_numbers[n] = self.cc_number(n)
            cc_values[n] = self.cc_value(n)

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
