"""
Utility functions and mappings for the Octatrack API.
"""

from typing import Tuple, Optional

from .enums import TrigCondition


# =============================================================================
# Generic Quantization
# =============================================================================

def quantize_to_nearest(
    value: float,
    valid_values: Tuple,
    clamp: Optional[Tuple[float, float]] = None
) -> float:
    """
    Quantize a value to the nearest value in a tuple of valid values.

    Args:
        value: The value to quantize
        valid_values: Tuple of valid values to snap to (must be sorted)
        clamp: Optional (min, max) tuple to clamp before quantizing

    Returns:
        The nearest valid value
    """
    if clamp:
        if value <= clamp[0]:
            return valid_values[0]
        if value >= clamp[1]:
            return valid_values[-1]

    best = valid_values[0]
    best_dist = abs(value - best)
    for v in valid_values[1:]:
        dist = abs(value - v)
        if dist < best_dist:
            best = v
            best_dist = dist
    return best


# =============================================================================
# Note Length Quantization
# =============================================================================

# Valid note length values (MIDI ticks at 24 PPQN)
# Includes 1/32 (3), all integer 16ths (multiples of 6), and infinity (127)
NOTE_LENGTH_VALUES = (
    3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 127
)


def quantize_note_length(value: int) -> int:
    """
    Quantize a raw value to the nearest valid NoteLength.

    Valid values: 3 (1/32), multiples of 6 from 6-126, and 127 (infinity).

    Args:
        value: Raw note length value (0-127)

    Returns:
        Nearest valid NoteLength value (3, 6, 12, ... 126, 127)
    """
    return int(quantize_to_nearest(value, NOTE_LENGTH_VALUES, clamp=(3, 127)))


# =============================================================================
# Probability Quantization
# =============================================================================

# Valid probability values (matching TrigCondition PERCENT_* enums)
PROBABILITY_VALUES = (
    0.01, 0.02, 0.04, 0.06, 0.09, 0.13, 0.19, 0.25, 0.33, 0.41,
    0.50, 0.59, 0.67, 0.75, 0.81, 0.87, 0.91, 0.94, 0.96, 0.98, 0.99
)

# Mapping from probability TrigConditions to float values
PROBABILITY_MAP = {
    TrigCondition.PERCENT_1: 0.01,
    TrigCondition.PERCENT_2: 0.02,
    TrigCondition.PERCENT_4: 0.04,
    TrigCondition.PERCENT_6: 0.06,
    TrigCondition.PERCENT_9: 0.09,
    TrigCondition.PERCENT_13: 0.13,
    TrigCondition.PERCENT_19: 0.19,
    TrigCondition.PERCENT_25: 0.25,
    TrigCondition.PERCENT_33: 0.33,
    TrigCondition.PERCENT_41: 0.41,
    TrigCondition.PERCENT_50: 0.50,
    TrigCondition.PERCENT_59: 0.59,
    TrigCondition.PERCENT_67: 0.67,
    TrigCondition.PERCENT_75: 0.75,
    TrigCondition.PERCENT_81: 0.81,
    TrigCondition.PERCENT_87: 0.87,
    TrigCondition.PERCENT_91: 0.91,
    TrigCondition.PERCENT_94: 0.94,
    TrigCondition.PERCENT_96: 0.96,
    TrigCondition.PERCENT_98: 0.98,
    TrigCondition.PERCENT_99: 0.99,
}

# Reverse mapping: probability float -> TrigCondition
_PROBABILITY_TO_CONDITION = {v: k for k, v in PROBABILITY_MAP.items()}


def quantize_probability(value: float) -> float:
    """
    Quantize a probability value to the nearest valid probability.

    Args:
        value: Probability value (0.0-1.0)

    Returns:
        Nearest valid probability value
    """
    return quantize_to_nearest(value, PROBABILITY_VALUES, clamp=(0.01, 0.99))


def probability_to_condition(value: float) -> TrigCondition:
    """
    Convert a probability value to the nearest TrigCondition.

    Args:
        value: Probability value (0.0-1.0)

    Returns:
        Matching TrigCondition enum
    """
    quantized = quantize_probability(value)
    return _PROBABILITY_TO_CONDITION[quantized]
