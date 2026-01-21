"""
MidiStep - standalone step object for MIDI pattern tracks.

This is a standalone object that owns its data and can be created
with constructor arguments or read from binary data.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict

from ...._io import MIDI_PLOCK_SIZE, PLOCK_DISABLED, MidiPlockOffset
from ...utils import quantize_note_length


class MidiStep:
    """
    Individual step within a MIDI pattern track.

    This is a standalone object that can be created with constructor arguments
    or read from binary data. It owns its data.

    Each step has:
    - Active state (whether it triggers)
    - Trigless state (envelope-only trigger)
    - Condition (when to trigger: FILL, probability, etc.)
    - MIDI p-locks (note, velocity, length, pitch_bend, aftertouch, CCs)

    Usage:
        # Create with constructor arguments
        step = MidiStep(
            step_num=1,
            active=True,
            note=60,        # Middle C
            velocity=100,
            length=6,       # 1/16 note
        )

        # Read from binary (called by MidiPatternTrack)
        step = MidiStep.read(step_num, active, trigless, condition_data, plock_data)

        # Write to binary
        active, trigless, condition_data, plock_data = step.write()
    """

    def __init__(
        self,
        step_num: int = 1,
        active: bool = False,
        trigless: bool = False,
        condition: Optional[int] = None,
        probability: Optional[float] = None,
        # MIDI p-locks
        note: Optional[int] = None,
        velocity: Optional[int] = None,
        length: Optional[int] = None,
        pitch_bend: Optional[int] = None,
        aftertouch: Optional[int] = None,
    ):
        """
        Create a MidiStep with optional parameter overrides.

        Args:
            step_num: Step number (1-64)
            active: Whether this step triggers
            trigless: Whether this is an envelope-only (trigless) trigger
            condition: Trig condition (TrigCondition enum value)
            probability: Trigger probability (0.0-1.0), sets condition
            note: MIDI note (0-127, 60=Middle C)
            velocity: MIDI velocity (0-127)
            length: Note length (quantized to valid NoteLength values)
            pitch_bend: Pitch bend (0-127, 64=center)
            aftertouch: Aftertouch (0-127)
        """
        self._step_num = step_num
        self._active = active
        self._trigless = trigless

        # Condition data: 2 bytes [microtiming_count, condition_microtiming]
        self._condition_data = bytearray(2)

        # P-lock data: 32 bytes (MIDI_PLOCK_SIZE)
        # Initialize all to disabled (255)
        self._plock_data = bytearray([PLOCK_DISABLED] * MIDI_PLOCK_SIZE)

        # Apply condition
        if condition is not None:
            self.condition = condition
        elif probability is not None:
            self.probability = probability

        # Apply MIDI p-locks
        if note is not None:
            self.note = note
        if velocity is not None:
            self.velocity = velocity
        if length is not None:
            self.length = length
        if pitch_bend is not None:
            self.pitch_bend = pitch_bend
        if aftertouch is not None:
            self.aftertouch = aftertouch

    @classmethod
    def read(
        cls,
        step_num: int,
        active: bool,
        trigless: bool,
        condition_data: bytes,
        plock_data: bytes,
    ) -> "MidiStep":
        """
        Read a MidiStep from extracted binary data.

        Args:
            step_num: Step number (1-64)
            active: Whether step is active (from trig mask)
            trigless: Whether step is trigless (from trigless mask)
            condition_data: 2 bytes of condition/microtiming data
            plock_data: 32 bytes of MIDI p-lock data

        Returns:
            MidiStep instance
        """
        instance = cls.__new__(cls)
        instance._step_num = step_num
        instance._active = active
        instance._trigless = trigless
        instance._condition_data = bytearray(condition_data[:2])
        instance._plock_data = bytearray(plock_data[:MIDI_PLOCK_SIZE])
        return instance

    def write(self) -> Tuple[bool, bool, bytes, bytes]:
        """
        Write this MidiStep to binary data components.

        Returns:
            Tuple of (active, trigless, condition_data, plock_data)
            - active: bool for trig mask
            - trigless: bool for trigless mask
            - condition_data: 2 bytes
            - plock_data: 32 bytes
        """
        return (
            self._active,
            self._trigless,
            bytes(self._condition_data),
            bytes(self._plock_data),
        )

    def clone(self) -> "MidiStep":
        """
        Create a copy of this MidiStep.

        Returns:
            New MidiStep with copied data
        """
        instance = MidiStep.__new__(MidiStep)
        instance._step_num = self._step_num
        instance._active = self._active
        instance._trigless = self._trigless
        instance._condition_data = bytearray(self._condition_data)
        instance._plock_data = bytearray(self._plock_data)
        return instance

    # === Basic properties ===

    @property
    def step_num(self) -> int:
        """Get the step number (1-64)."""
        return self._step_num

    @property
    def active(self) -> bool:
        """Get/set whether this step has an active trigger."""
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value

    @property
    def trigless(self) -> bool:
        """Get/set whether this step has a trigless (envelope-only) trigger."""
        return self._trigless

    @trigless.setter
    def trigless(self, value: bool):
        self._trigless = value

    # === Condition properties ===

    @property
    def condition(self):
        """
        Get/set the trig condition for this step.

        The condition determines when this step triggers (FILL, probability, etc.).
        """
        from ...enums import TrigCondition
        # Condition is in lower 7 bits of byte 1
        raw_value = self._condition_data[1] & 0x7F
        try:
            return TrigCondition(raw_value)
        except ValueError:
            return TrigCondition.NONE

    @condition.setter
    def condition(self, value):
        # Preserve microtiming bit (bit 7), set condition in lower 7 bits
        micro_timing_bit = self._condition_data[1] & 0x80
        self._condition_data[1] = micro_timing_bit | (int(value) & 0x7F)

    @property
    def probability(self) -> Optional[float]:
        """
        Get/set probability for this step as a float (0.0-1.0).

        Returns the probability if a probability condition is set,
        or None if no probability condition is active.

        Setting a value sets the closest matching probability condition.
        Set to None or 1.0 to clear probability (always trigger).
        """
        from ...utils import PROBABILITY_MAP
        return PROBABILITY_MAP.get(self.condition)

    @probability.setter
    def probability(self, value: Optional[float]):
        from ...enums import TrigCondition
        from ...utils import probability_to_condition

        if value is None or value >= 1.0:
            self.condition = TrigCondition.NONE
            return

        self.condition = probability_to_condition(value)

    # === P-lock methods ===

    def _get_plock(self, offset: int) -> Optional[int]:
        """Get a p-lock value. Returns None if disabled (255)."""
        value = self._plock_data[offset]
        return None if value == PLOCK_DISABLED else value

    def _set_plock(self, offset: int, value: Optional[int]):
        """Set a p-lock value. None disables the p-lock."""
        if value is None:
            self._plock_data[offset] = PLOCK_DISABLED
        else:
            self._plock_data[offset] = value & 0xFF

    # === MIDI p-lock properties ===

    @property
    def note(self) -> Optional[int]:
        """
        Get/set p-locked MIDI note for this step.

        Value range: 0-127 (60 = Middle C)
        Returns None if no p-lock is set (uses Part default).
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

    @property
    def pitch_bend(self) -> Optional[int]:
        """
        Get/set p-locked MIDI pitch bend for this step.

        Value range: 0-127 (64 = center, no bend)
        Returns None if no p-lock is set (uses Part default).
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
        """
        return self._get_plock(MidiPlockOffset.AFTERTOUCH)

    @aftertouch.setter
    def aftertouch(self, value: Optional[int]):
        self._set_plock(MidiPlockOffset.AFTERTOUCH, value)

    # === CC access ===

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
        Convert step state to dictionary.

        Returns dict with step_num, active, trigless, condition, and MIDI p-locks.
        """
        from ...enums import TrigCondition

        result = {
            "step": self._step_num,
            "active": self._active,
            "trigless": self._trigless,
        }

        # Only include condition if not NONE
        if self.condition != TrigCondition.NONE:
            result["condition"] = self.condition.name

        # Only include probability if set
        if self.probability is not None:
            result["probability"] = self.probability

        # Include MIDI p-locks if set
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
        cc_values: Dict[int, int] = {}
        for n in range(1, 11):
            val = self.cc(n)
            if val is not None:
                cc_values[n] = val
        if cc_values:
            result["cc"] = cc_values

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "MidiStep":
        """
        Create a MidiStep from a dictionary.

        Args:
            data: Dictionary with step properties

        Returns:
            MidiStep instance
        """
        from ...enums import TrigCondition

        kwargs = {
            "step_num": data.get("step", 1),
            "active": data.get("active", False),
            "trigless": data.get("trigless", False),
        }

        if "condition" in data:
            cond = data["condition"]
            if isinstance(cond, str):
                kwargs["condition"] = TrigCondition[cond]
            else:
                kwargs["condition"] = cond

        if "probability" in data:
            kwargs["probability"] = data["probability"]

        if "note" in data:
            kwargs["note"] = data["note"]

        if "velocity" in data:
            kwargs["velocity"] = data["velocity"]

        if "length" in data:
            kwargs["length"] = data["length"]

        if "pitch_bend" in data:
            kwargs["pitch_bend"] = data["pitch_bend"]

        if "aftertouch" in data:
            kwargs["aftertouch"] = data["aftertouch"]

        instance = cls(**kwargs)

        # Apply CC values
        if "cc" in data:
            for n, val in data["cc"].items():
                instance.set_cc(int(n), val)

        return instance

    def __eq__(self, other) -> bool:
        """Check equality based on all data."""
        if not isinstance(other, MidiStep):
            return NotImplemented
        return (
            self._step_num == other._step_num
            and self._active == other._active
            and self._trigless == other._trigless
            and self._condition_data == other._condition_data
            and self._plock_data == other._plock_data
        )

    def __repr__(self) -> str:
        return f"MidiStep(step={self._step_num}, active={self._active})"
