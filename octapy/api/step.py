"""
Step classes for individual steps within pattern tracks.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .._io import (
    AudioTrackOffset,
    PlockOffset,
    MidiTrackTrigsOffset,
    MidiPlockOffset,
    PLOCK_SIZE,
    PLOCK_DISABLED,
    MIDI_PLOCK_SIZE,
)


# =============================================================================
# Trig Mask Utilities
# =============================================================================

def _trig_mask_to_steps(data: bytearray, offset: int) -> List[int]:
    """Convert 8-byte trig mask to list of step numbers (1-64)."""
    steps = []

    # Page 1 (bytes 6-7, reversed: byte 7 = steps 1-8, byte 6 = steps 9-16)
    for bit in range(8):
        if data[offset + 7] & (1 << bit):
            steps.append(bit + 1)
    for bit in range(8):
        if data[offset + 6] & (1 << bit):
            steps.append(bit + 9)

    # Page 2 (bytes 4-5)
    for bit in range(8):
        if data[offset + 4] & (1 << bit):
            steps.append(bit + 17)
    for bit in range(8):
        if data[offset + 5] & (1 << bit):
            steps.append(bit + 25)

    # Page 3 (bytes 2-3)
    for bit in range(8):
        if data[offset + 2] & (1 << bit):
            steps.append(bit + 33)
    for bit in range(8):
        if data[offset + 3] & (1 << bit):
            steps.append(bit + 41)

    # Page 4 (bytes 0-1)
    for bit in range(8):
        if data[offset + 0] & (1 << bit):
            steps.append(bit + 49)
    for bit in range(8):
        if data[offset + 1] & (1 << bit):
            steps.append(bit + 57)

    return sorted(steps)


def _steps_to_trig_mask(data: bytearray, offset: int, steps: List[int]):
    """Convert list of step numbers (1-64) to 8-byte trig mask."""
    # Clear existing mask
    for i in range(8):
        data[offset + i] = 0

    for step in steps:
        if step < 1 or step > 64:
            continue

        if step <= 8:
            data[offset + 7] |= (1 << (step - 1))
        elif step <= 16:
            data[offset + 6] |= (1 << (step - 9))
        elif step <= 24:
            data[offset + 4] |= (1 << (step - 17))
        elif step <= 32:
            data[offset + 5] |= (1 << (step - 25))
        elif step <= 40:
            data[offset + 2] |= (1 << (step - 33))
        elif step <= 48:
            data[offset + 3] |= (1 << (step - 41))
        elif step <= 56:
            data[offset + 0] |= (1 << (step - 49))
        else:
            data[offset + 1] |= (1 << (step - 57))


def _step_to_bit_position(step: int) -> tuple:
    """
    Convert step number (1-64) to (byte_index, bit_position) within trig mask.

    Returns byte index (0-7) relative to the trig mask start.
    """
    if step <= 8:
        return (7, step - 1)
    elif step <= 16:
        return (6, step - 9)
    elif step <= 24:
        return (4, step - 17)
    elif step <= 32:
        return (5, step - 25)
    elif step <= 40:
        return (2, step - 33)
    elif step <= 48:
        return (3, step - 41)
    elif step <= 56:
        return (0, step - 49)
    else:
        return (1, step - 57)


# =============================================================================
# BaseStep Class
# =============================================================================

class BaseStep(ABC):
    """
    Abstract base class for individual steps within pattern tracks.

    Provides shared functionality for trig state, conditions, p-locks,
    and probability. Subclasses provide offset constants.
    """

    def __init__(self, pattern_track, step_num: int):
        self._pattern_track = pattern_track
        self._step_num = step_num  # 1-64

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._pattern_track._pattern._bank._bank_file._data

    @property
    @abstractmethod
    def _trig_offset(self) -> int:
        """Offset to TRIG_TRIGGER within the track."""
        pass

    @property
    @abstractmethod
    def _trigless_offset(self) -> int:
        """Offset to TRIG_TRIGLESS within the track."""
        pass

    @property
    @abstractmethod
    def _plocks_offset(self) -> int:
        """Offset to PLOCKS within the track."""
        pass

    @property
    @abstractmethod
    def _plock_size(self) -> int:
        """Size of each step's p-lock data."""
        pass

    @property
    @abstractmethod
    def _conditions_offset(self) -> int:
        """Offset to TRIG_CONDITIONS within the track."""
        pass

    # === Shared trig bit methods ===

    def _get_bit_at_offset(self, trig_base_offset: int) -> bool:
        """Get a single trig bit at the given base offset."""
        track_offset = self._pattern_track._track_offset()
        byte_idx, bit_pos = _step_to_bit_position(self._step_num)
        offset = track_offset + trig_base_offset + byte_idx
        return bool(self._data[offset] & (1 << bit_pos))

    def _set_bit_at_offset(self, trig_base_offset: int, value: bool):
        """Set a single trig bit at the given base offset."""
        track_offset = self._pattern_track._track_offset()
        byte_idx, bit_pos = _step_to_bit_position(self._step_num)
        offset = track_offset + trig_base_offset + byte_idx
        if value:
            self._data[offset] |= (1 << bit_pos)
        else:
            self._data[offset] &= ~(1 << bit_pos)

    # === Shared p-lock methods ===

    def _plock_offset_for(self, param_offset: int) -> int:
        """Get the absolute byte offset for a p-lock parameter on this step."""
        track_offset = self._pattern_track._track_offset()
        step_index = self._step_num - 1  # 0-indexed
        return track_offset + self._plocks_offset + (step_index * self._plock_size) + param_offset

    def _get_plock(self, param_offset: int) -> Optional[int]:
        """Get a p-lock value. Returns None if disabled (255)."""
        offset = self._plock_offset_for(param_offset)
        value = self._data[offset]
        return None if value == PLOCK_DISABLED else value

    def _set_plock(self, param_offset: int, value: Optional[int]):
        """Set a p-lock value. None disables the p-lock."""
        offset = self._plock_offset_for(param_offset)
        if value is None:
            self._data[offset] = PLOCK_DISABLED
        else:
            self._data[offset] = value & 0xFF

    # === Shared condition methods ===

    def _condition_byte_offset(self) -> int:
        """Get the absolute byte offset for trig condition data on this step."""
        track_offset = self._pattern_track._track_offset()
        step_index = self._step_num - 1  # 0-indexed
        # Each step has 2 bytes: [count/microtiming, condition/microtiming]
        return track_offset + self._conditions_offset + (step_index * 2) + 1

    # === Trig state properties ===

    @property
    def active(self) -> bool:
        """Get/set whether this step has an active trigger."""
        return self._get_bit_at_offset(self._trig_offset)

    @active.setter
    def active(self, value: bool):
        self._set_bit_at_offset(self._trig_offset, value)

    @property
    def trigless(self) -> bool:
        """Get/set whether this step has a trigless (envelope) trigger."""
        return self._get_bit_at_offset(self._trigless_offset)

    @trigless.setter
    def trigless(self, value: bool):
        self._set_bit_at_offset(self._trigless_offset, value)

    # === Trig condition ===

    @property
    def condition(self):
        """
        Get/set the trig condition for this step.

        The condition determines when this step triggers (FILL, probability, etc.).
        """
        from .enums import TrigCondition
        offset = self._condition_byte_offset()
        # Condition is stored in lower 7 bits (0-64), bit 7 is micro-timing
        raw_value = self._data[offset] & 0x7F
        try:
            return TrigCondition(raw_value)
        except ValueError:
            return TrigCondition.NONE

    @condition.setter
    def condition(self, value):
        offset = self._condition_byte_offset()
        # Preserve micro-timing bit (bit 7), set condition in lower 7 bits
        current = self._data[offset]
        micro_timing_bit = current & 0x80
        self._data[offset] = micro_timing_bit | (int(value) & 0x7F)

    @property
    def probability(self) -> Optional[float]:
        """
        Get/set probability for this step as a float (0.0-1.0).

        Returns the probability if a probability condition is set,
        or None if no probability condition is active.

        Setting a value sets the closest matching probability condition.
        Set to None or 1.0 to clear probability (always trigger).
        """
        from .enums import PROBABILITY_MAP
        return PROBABILITY_MAP.get(self.condition)

    @probability.setter
    def probability(self, value: Optional[float]):
        from .enums import TrigCondition, PROBABILITY_MAP

        if value is None or value >= 1.0:
            self.condition = TrigCondition.NONE
            return

        # Find closest match
        closest = min(PROBABILITY_MAP.items(), key=lambda x: abs(x[1] - value))
        self.condition = closest[0]


# =============================================================================
# AudioStep Class
# =============================================================================

class AudioStep(BaseStep):
    """
    Individual step within an audio pattern track.

    Provides access to step properties including active state, trigless state,
    condition, and p-locks (per-step parameter values).

    Usage:
        step = pattern.track(1).step(5)
        step.active = True
        step.condition = TrigCondition.FILL
        step.volume = 100  # P-lock volume
        step.pitch = 64    # P-lock pitch (64 = no transpose)
    """

    @property
    def _trig_offset(self) -> int:
        return AudioTrackOffset.TRIG_TRIGGER

    @property
    def _trigless_offset(self) -> int:
        return AudioTrackOffset.TRIG_TRIGLESS

    @property
    def _plocks_offset(self) -> int:
        return AudioTrackOffset.PLOCKS

    @property
    def _plock_size(self) -> int:
        return PLOCK_SIZE

    @property
    def _conditions_offset(self) -> int:
        return AudioTrackOffset.TRIG_CONDITIONS

    # === Audio P-lock properties ===

    @property
    def volume(self) -> Optional[int]:
        """
        Get/set p-locked volume for this step.

        Value range: 0-127 (0 = silent, 127 = max)
        Returns None if no p-lock is set (uses track default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(PlockOffset.AMP_VOL)

    @volume.setter
    def volume(self, value: Optional[int]):
        self._set_plock(PlockOffset.AMP_VOL, value)

    @property
    def pitch(self) -> Optional[int]:
        """
        Get/set p-locked pitch/note for this step.

        Value range: 0-127 (64 = no transpose, <64 = lower, >64 = higher)
        This is the PTCH parameter on the Playback page.
        Returns None if no p-lock is set (uses track default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(PlockOffset.MACHINE_PARAM1)

    @pitch.setter
    def pitch(self, value: Optional[int]):
        self._set_plock(PlockOffset.MACHINE_PARAM1, value)

    @property
    def sample_lock(self) -> Optional[int]:
        """
        Get/set p-locked sample slot for this step (Flex machines).

        Value range: 0-127 (0-indexed slot number)
        Returns None if no sample lock is set.
        Set to None to clear the sample lock.
        """
        return self._get_plock(PlockOffset.FLEX_SLOT_ID)

    @sample_lock.setter
    def sample_lock(self, value: Optional[int]):
        self._set_plock(PlockOffset.FLEX_SLOT_ID, value)


# =============================================================================
# MidiStep Class
# =============================================================================

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

        Value range: 0-127 (6 = 1/16 note)
        Returns None if no p-lock is set (uses Part default).
        Set to None to clear the p-lock.
        """
        return self._get_plock(MidiPlockOffset.LENGTH)

    @length.setter
    def length(self, value: Optional[int]):
        self._set_plock(MidiPlockOffset.LENGTH, value)

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
