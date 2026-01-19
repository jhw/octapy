"""
MidiStep - MIDI track step class.
"""

from __future__ import annotations

from typing import Optional

from ..._io import (
    MidiTrackTrigsOffset,
    MidiPlockOffset,
    MIDI_PLOCK_SIZE,
)
from ..utils import quantize_note_length
from .base import BaseStep


class MidiStep(BaseStep):
    """
    Individual step within a MIDI pattern track.

    Provides access to step properties including active state, trigless state,
    condition, and MIDI-specific p-locks (note, velocity, length).

    Usage:
        step = pattern.midi_track(1).step(5)
        step.active = True
        step.note = 60       # Middle C
        step.velocity = 100  # Note velocity
        step.length = 6      # 1/16 note length
    """

    @property
    def _trig_offset(self) -> int:
        return MidiTrackTrigsOffset.TRIG_TRIGGER

    @property
    def _trigless_offset(self) -> int:
        return MidiTrackTrigsOffset.TRIG_TRIGLESS

    @property
    def _plocks_offset(self) -> int:
        return MidiTrackTrigsOffset.PLOCKS

    @property
    def _plock_size(self) -> int:
        return MIDI_PLOCK_SIZE

    @property
    def _conditions_offset(self) -> int:
        return MidiTrackTrigsOffset.TRIG_CONDITIONS

    # === MIDI P-lock properties ===

    @property
    def note(self) -> Optional[int]:
        """
        Get/set p-locked MIDI note for this step.

        Value range: 0-127 (60 = Middle C)
        Returns None if no p-lock is set (uses Part default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(MidiPlockOffset.NOTE)

    @note.setter
    def note(self, value: Optional[int]):
        self._set_plock(MidiPlockOffset.NOTE, value)

    @property
    def velocity(self) -> Optional[int]:
        """
        Get/set p-locked MIDI velocity for this step.

        Value range: 0-127
        Returns None if no p-lock is set (uses Part default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(MidiPlockOffset.VELOCITY)

    @velocity.setter
    def velocity(self, value: Optional[int]):
        self._set_plock(MidiPlockOffset.VELOCITY, value)

    @property
    def length(self) -> Optional[int]:
        """
        Get/set p-locked MIDI note length for this step.

        Values are quantized to valid NoteLength values:
        3 (1/32), 6 (1/16), 12 (1/8), ... 126 (21/16), 127 (infinity)

        Returns None if no p-lock is set (uses Part default).
        Set to None to clear the p-lock.
        """
        raw = self._get_plock(MidiPlockOffset.LENGTH)
        if raw is None:
            return None
        return quantize_note_length(raw)

    @length.setter
    def length(self, value: Optional[int]):
        if value is None:
            self._set_plock(MidiPlockOffset.LENGTH, None)
        else:
            quantized = quantize_note_length(value)
            self._set_plock(MidiPlockOffset.LENGTH, quantized)

    # === MIDI CC P-lock properties ===

    @property
    def pitch_bend(self) -> Optional[int]:
        """
        Get/set p-locked MIDI pitch bend for this step.

        Value range: 0-127 (64 = center, no bend)
        Returns None if no p-lock is set (uses Part default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(MidiPlockOffset.PITCH_BEND)

    @pitch_bend.setter
    def pitch_bend(self, value: Optional[int]):
        self._set_plock(MidiPlockOffset.PITCH_BEND, value)

    @property
    def aftertouch(self) -> Optional[int]:
        """
        Get/set p-locked MIDI aftertouch for this step.

        Value range: 0-127
        Returns None if no p-lock is set (uses Part default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(MidiPlockOffset.AFTERTOUCH)

    @aftertouch.setter
    def aftertouch(self, value: Optional[int]):
        self._set_plock(MidiPlockOffset.AFTERTOUCH, value)

    def cc(self, n: int) -> Optional[int]:
        """
        Get p-locked CC value for slot n (1-10).

        Args:
            n: CC slot number (1-10)

        Returns:
            CC value (0-127), or None if no p-lock is set
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        return self._get_plock(19 + n)  # CC1 is at offset 20

    def set_cc(self, n: int, value: Optional[int]):
        """
        Set p-locked CC value for slot n (1-10).

        Args:
            n: CC slot number (1-10)
            value: CC value (0-127), or None to clear p-lock
        """
        if n < 1 or n > 10:
            raise ValueError(f"CC slot must be 1-10, got {n}")
        self._set_plock(19 + n, value)  # CC1 is at offset 20

    def to_dict(self) -> dict:
        """
        Convert step state to dictionary including MIDI p-locks.

        Extends base to_dict with note, velocity, length, pitch_bend,
        aftertouch, and CC values.
        """
        result = super().to_dict()
        # Only include p-locks if set
        if self.note is not None:
            result["note"] = self.note
        if self.velocity is not None:
            result["velocity"] = self.velocity
        if self.length is not None:
            result["length"] = self.length
        if self.pitch_bend is not None:
            result["pitch_bend"] = self.pitch_bend
        if self.aftertouch is not None:
            result["aftertouch"] = self.aftertouch
        # Check CC slots 1-10
        cc_values = {}
        for n in range(1, 11):
            val = self.cc(n)
            if val is not None:
                cc_values[n] = val
        if cc_values:
            result["cc"] = cc_values
        return result
