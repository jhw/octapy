"""
AudioStep - standalone step object for audio pattern tracks.

This is a standalone object that owns its data and can be created
with constructor arguments or read from binary data.
"""

from __future__ import annotations

from typing import Optional, Tuple

from ..._io import PLOCK_SIZE, PLOCK_DISABLED, PlockOffset


class AudioStep:
    """
    Individual step within an audio pattern track.

    This is a standalone object that can be created with constructor arguments
    or read from binary data. It owns its data.

    Each step has:
    - Active state (whether it triggers)
    - Trigless state (envelope-only trigger)
    - Condition (when to trigger: FILL, probability, etc.)
    - P-locks (parameter locks for any track parameter)

    Usage:
        # Create with constructor arguments
        step = AudioStep(
            step_num=1,
            active=True,
            condition=TrigCondition.FILL,
            volume=100,
        )

        # Read from binary (called by AudioPatternTrack)
        step = AudioStep.read(step_num, active, trigless, condition_data, plock_data)

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
        # Common p-locks
        volume: Optional[int] = None,
        pitch: Optional[int] = None,
        sample_lock: Optional[int] = None,
    ):
        """
        Create an AudioStep with optional parameter overrides.

        Args:
            step_num: Step number (1-64)
            active: Whether this step triggers
            trigless: Whether this is an envelope-only (trigless) trigger
            condition: Trig condition (TrigCondition enum value)
            probability: Trigger probability (0.0-1.0), sets condition
            volume: P-locked volume (0-127)
            pitch: P-locked pitch (0-127, 64=center)
            sample_lock: P-locked sample slot
        """
        self._step_num = step_num
        self._active = active
        self._trigless = trigless

        # Condition data: 2 bytes [microtiming_count, condition_microtiming]
        # Condition is in bits 0-6 of byte 1, bit 7 is microtiming flag
        self._condition_data = bytearray(2)

        # P-lock data: 32 bytes (or PLOCK_SIZE)
        # Initialize all to disabled (255)
        self._plock_data = bytearray([PLOCK_DISABLED] * PLOCK_SIZE)

        # Apply condition
        if condition is not None:
            self.condition = condition
        elif probability is not None:
            self.probability = probability

        # Apply p-locks
        if volume is not None:
            self.volume = volume
        if pitch is not None:
            self.pitch = pitch
        if sample_lock is not None:
            self.sample_lock = sample_lock

    @classmethod
    def read(
        cls,
        step_num: int,
        active: bool,
        trigless: bool,
        condition_data: bytes,
        plock_data: bytes,
    ) -> "AudioStep":
        """
        Read an AudioStep from extracted binary data.

        Args:
            step_num: Step number (1-64)
            active: Whether step is active (from trig mask)
            trigless: Whether step is trigless (from trigless mask)
            condition_data: 2 bytes of condition/microtiming data
            plock_data: 32 bytes of p-lock data

        Returns:
            AudioStep instance
        """
        instance = cls.__new__(cls)
        instance._step_num = step_num
        instance._active = active
        instance._trigless = trigless
        instance._condition_data = bytearray(condition_data[:2])
        instance._plock_data = bytearray(plock_data[:PLOCK_SIZE])
        return instance

    def write(self) -> Tuple[bool, bool, bytes, bytes]:
        """
        Write this AudioStep to binary data components.

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

    def clone(self) -> "AudioStep":
        """
        Create a copy of this AudioStep.

        Returns:
            New AudioStep with copied data
        """
        instance = AudioStep.__new__(AudioStep)
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
        from ..enums import TrigCondition
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
        from ..utils import PROBABILITY_MAP
        return PROBABILITY_MAP.get(self.condition)

    @probability.setter
    def probability(self, value: Optional[float]):
        from ..enums import TrigCondition
        from ..utils import probability_to_condition

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

    # === Common p-lock properties ===

    @property
    def volume(self) -> Optional[int]:
        """
        Get/set p-locked volume for this step.

        Value range: 0-127
        Returns None if no p-lock is set (uses Part default).
        """
        return self._get_plock(PlockOffset.AMP_VOL)

    @volume.setter
    def volume(self, value: Optional[int]):
        self._set_plock(PlockOffset.AMP_VOL, value)

    @property
    def pitch(self) -> Optional[int]:
        """
        Get/set p-locked pitch for this step.

        Value range: 0-127 (64 = center/no transpose)
        Returns None if no p-lock is set (uses Part default).
        """
        return self._get_plock(PlockOffset.MACHINE_PARAM1)

    @pitch.setter
    def pitch(self, value: Optional[int]):
        self._set_plock(PlockOffset.MACHINE_PARAM1, value)

    @property
    def sample_lock(self) -> Optional[int]:
        """
        Get/set p-locked sample slot for this step.

        This allows changing the sample played on a per-step basis.
        Returns None if no p-lock is set (uses Part default).
        """
        return self._get_plock(PlockOffset.FLEX_SLOT_ID)

    @sample_lock.setter
    def sample_lock(self, value: Optional[int]):
        self._set_plock(PlockOffset.FLEX_SLOT_ID, value)

    def to_dict(self) -> dict:
        """
        Convert step state to dictionary.

        Returns dict with step_num, active, trigless, and any set p-locks.
        """
        from ..enums import TrigCondition

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

        # Include p-locks if set
        if self.volume is not None:
            result["volume"] = self.volume
        if self.pitch is not None:
            result["pitch"] = self.pitch
        if self.sample_lock is not None:
            result["sample_lock"] = self.sample_lock

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AudioStep":
        """
        Create an AudioStep from a dictionary.

        Args:
            data: Dictionary with step properties

        Returns:
            AudioStep instance
        """
        from ..enums import TrigCondition

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

        if "volume" in data:
            kwargs["volume"] = data["volume"]

        if "pitch" in data:
            kwargs["pitch"] = data["pitch"]

        if "sample_lock" in data:
            kwargs["sample_lock"] = data["sample_lock"]

        return cls(**kwargs)

    def __eq__(self, other) -> bool:
        """Check equality based on all data."""
        if not isinstance(other, AudioStep):
            return NotImplemented
        return (
            self._step_num == other._step_num
            and self._active == other._active
            and self._trigless == other._trigless
            and self._condition_data == other._condition_data
            and self._plock_data == other._plock_data
        )

    def __repr__(self) -> str:
        return f"AudioStep(step={self._step_num}, active={self._active})"
