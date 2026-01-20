"""
Trig mask utility functions for pattern tracks.

These functions convert between step lists (1-64) and the 8-byte trig mask
format used in the Octatrack binary format.
"""


def _step_to_bit_position(step: int) -> tuple:
    """
    Convert a step number (1-64) to (byte_index, bit_position) in the trig mask.

    The OT uses a specific bit layout across 8 bytes:
    - Bytes 6-7: Steps 1-16 (Page 1)
    - Bytes 4-5: Steps 17-32 (Page 2)
    - Bytes 2-3: Steps 33-48 (Page 3)
    - Bytes 0-1: Steps 49-64 (Page 4)

    Within each 2-byte pair, the second byte holds lower steps.
    """
    if step < 1 or step > 64:
        raise ValueError(f"Step must be 1-64, got {step}")

    # Determine which page (0-3)
    page = (step - 1) // 16
    # Position within page (0-15)
    pos_in_page = (step - 1) % 16

    # Byte pairs are in reverse order (page 0 is bytes 6-7)
    byte_pair_start = 6 - (page * 2)

    # Within the pair, low byte (offset +1) is for steps 1-8, high byte (offset +0) for 9-16
    if pos_in_page < 8:
        byte_index = byte_pair_start + 1
        bit_position = pos_in_page
    else:
        byte_index = byte_pair_start
        bit_position = pos_in_page - 8

    return byte_index, bit_position


def _trig_mask_to_steps(data: bytes, offset: int = 0) -> list:
    """
    Convert 8-byte trig mask to list of step numbers (1-64).

    Args:
        data: Binary data containing the trig mask
        offset: Offset to the start of the 8-byte trig mask

    Returns:
        Sorted list of active step numbers (1-64)
    """
    steps = []

    # Page 1 (bytes 6-7): Steps 1-16
    for bit in range(8):
        if data[offset + 7] & (1 << bit):
            steps.append(bit + 1)
    for bit in range(8):
        if data[offset + 6] & (1 << bit):
            steps.append(bit + 9)

    # Page 2 (bytes 4-5): Steps 17-32
    for bit in range(8):
        if data[offset + 5] & (1 << bit):
            steps.append(bit + 17)
    for bit in range(8):
        if data[offset + 4] & (1 << bit):
            steps.append(bit + 25)

    # Page 3 (bytes 2-3): Steps 33-48
    for bit in range(8):
        if data[offset + 3] & (1 << bit):
            steps.append(bit + 33)
    for bit in range(8):
        if data[offset + 2] & (1 << bit):
            steps.append(bit + 41)

    # Page 4 (bytes 0-1): Steps 49-64
    for bit in range(8):
        if data[offset + 1] & (1 << bit):
            steps.append(bit + 49)
    for bit in range(8):
        if data[offset + 0] & (1 << bit):
            steps.append(bit + 57)

    return sorted(steps)


def _steps_to_trig_mask(data: bytearray, offset: int, steps: list):
    """
    Convert list of step numbers (1-64) to 8-byte trig mask.

    Args:
        data: Binary data (modified in place)
        offset: Offset to the start of the 8-byte trig mask
        steps: List of active step numbers (1-64)
    """
    # Clear existing mask
    for i in range(8):
        data[offset + i] = 0

    for step in steps:
        if step < 1 or step > 64:
            continue

        byte_index, bit_position = _step_to_bit_position(step)
        data[offset + byte_index] |= (1 << bit_position)
