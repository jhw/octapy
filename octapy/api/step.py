"""
Step class for individual steps within a PatternTrack.
"""

from typing import TYPE_CHECKING, List

from .._io import AudioTrackOffset

if TYPE_CHECKING:
    from .pattern import PatternTrack


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


# =============================================================================
# Step Class
# =============================================================================

class Step:
    """
    Individual step within a pattern track.

    Provides access to step properties including active state, trigless state,
    condition, and (future) p-locks.

    Usage:
        step = pattern.track(1).step(5)
        step.active = True
        step.condition = TrigCondition.FILL
    """

    def __init__(self, pattern_track: "PatternTrack", step_num: int):
        self._pattern_track = pattern_track
        self._step_num = step_num  # 1-64

    def _get_trig_bit_location(self) -> tuple:
        """Get (byte_offset, bit_position) for this step in the trig mask."""
        step = self._step_num
        base_offset = self._pattern_track._track_offset()

        # Calculate byte and bit position based on step number
        # Steps 1-8: byte 7, Steps 9-16: byte 6
        # Steps 17-24: byte 4, Steps 25-32: byte 5
        # Steps 33-40: byte 2, Steps 41-48: byte 3
        # Steps 49-56: byte 0, Steps 57-64: byte 1
        if step <= 8:
            return (base_offset + 7, step - 1)
        elif step <= 16:
            return (base_offset + 6, step - 9)
        elif step <= 24:
            return (base_offset + 4, step - 17)
        elif step <= 32:
            return (base_offset + 5, step - 25)
        elif step <= 40:
            return (base_offset + 2, step - 33)
        elif step <= 48:
            return (base_offset + 3, step - 41)
        elif step <= 56:
            return (base_offset + 0, step - 49)
        else:
            return (base_offset + 1, step - 57)

    def _get_bit(self, trig_type_offset: int) -> bool:
        """Get a single trig bit (active or trigless)."""
        data = self._pattern_track._pattern._bank._bank_file._data
        byte_offset, bit_pos = self._get_trig_bit_location()
        byte_offset += trig_type_offset
        return bool(data[byte_offset] & (1 << bit_pos))

    def _set_bit(self, trig_type_offset: int, value: bool):
        """Set a single trig bit (active or trigless)."""
        data = self._pattern_track._pattern._bank._bank_file._data
        byte_offset, bit_pos = self._get_trig_bit_location()
        byte_offset += trig_type_offset
        if value:
            data[byte_offset] |= (1 << bit_pos)
        else:
            data[byte_offset] &= ~(1 << bit_pos)

    @property
    def active(self) -> bool:
        """Get/set whether this step has an active trigger."""
        return self._get_bit(AudioTrackOffset.TRIG_TRIGGER)

    @active.setter
    def active(self, value: bool):
        self._set_bit(AudioTrackOffset.TRIG_TRIGGER, value)

    @property
    def trigless(self) -> bool:
        """Get/set whether this step has a trigless (envelope) trigger."""
        return self._get_bit(AudioTrackOffset.TRIG_TRIGLESS)

    @trigless.setter
    def trigless(self, value: bool):
        self._set_bit(AudioTrackOffset.TRIG_TRIGLESS, value)

    @property
    def condition(self) -> "TrigCondition":
        """Get/set the trig condition for this step."""
        from .base import TrigCondition
        # TODO: Implement condition storage once we map the offset
        # For now, return NONE
        return TrigCondition.NONE

    @condition.setter
    def condition(self, value: "TrigCondition"):
        # TODO: Implement condition storage once we map the offset
        pass
