"""
Enums, constants and exceptions for the Octatrack API.
"""

from enum import IntEnum


# === Slot limits ===
MAX_FLEX_SAMPLE_SLOTS = 128  # Slots 1-128 for user samples
MAX_STATIC_SAMPLE_SLOTS = 128  # Slots 1-128 (separate pool from flex)
RECORDER_SLOTS_START = 129  # Recorder buffer slots 129-136


# === Exceptions ===

class OctapyError(Exception):
    """Base exception for octapy errors."""
    pass


class SlotLimitExceeded(OctapyError):
    """Raised when trying to add more samples than available slots."""
    pass


class InvalidSlotNumber(OctapyError):
    """Raised when a slot number is out of valid range."""
    pass


# === Sample duration ===

class SampleDuration(IntEnum):
    """
    Sample duration in musical subdivisions.

    Used to normalize sample lengths based on BPM.
    At 120 BPM:
      - SIXTEENTH (1 step) = 125ms
      - EIGHTH (2 steps) = 250ms
      - THIRTY_SECOND (0.5 steps) = 62.5ms
    """
    THIRTY_SECOND = 8   # divisor: 60/bpm/8
    SIXTEENTH = 4       # divisor: 60/bpm/4
    EIGHTH = 2          # divisor: 60/bpm/2


# Machine types (for audio tracks in Parts)
class MachineType(IntEnum):
    """Machine types for audio tracks."""
    STATIC = 0
    FLEX = 1
    THRU = 2
    NEIGHBOR = 3
    PICKUP = 4


# Thru machine input selection
class ThruInput(IntEnum):
    """
    Input selection for Thru machine.

    Used with ThruPartTrack.in_ab and ThruPartTrack.in_cd to select
    which physical input(s) to route.
    """
    OFF = 0
    A_PLUS_B = 1  # A+B combined (stereo pair)
    A = 2         # Input A only (left)
    B = 3         # Input B only (right)
    A_B = 4       # A/B (both separate)


# FX types for audio tracks
class FX1Type(IntEnum):
    """FX1 slot effect types."""
    OFF = 0
    FILTER = 4
    SPATIALIZER = 5
    EQ = 12
    DJ_EQ = 13
    PHASER = 16
    FLANGER = 17
    CHORUS = 18
    COMB_FILTER = 19
    COMPRESSOR = 24
    LOFI = 25


class FX2Type(IntEnum):
    """FX2 slot effect types (includes delay/reverb)."""
    OFF = 0
    FILTER = 4
    SPATIALIZER = 5
    DELAY = 8
    EQ = 12
    DJ_EQ = 13
    PHASER = 16
    FLANGER = 17
    CHORUS = 18
    COMB_FILTER = 19
    PLATE_REVERB = 20
    SPRING_REVERB = 21
    DARK_REVERB = 22
    COMPRESSOR = 24
    LOFI = 25


# Pattern scale modes
class ScaleMode(IntEnum):
    """Pattern scale modes."""
    NORMAL = 0
    PER_TRACK = 1


class PatternScale(IntEnum):
    """Pattern playback speed multipliers."""
    X2 = 0       # 2x speed
    X3_2 = 1     # 3/2x speed
    X1 = 2       # 1x speed (default)
    X3_4 = 3     # 3/4x speed
    X1_2 = 4     # 1/2x speed
    X1_4 = 5     # 1/4x speed
    X1_8 = 6     # 1/8x speed


# Trig conditions for Steps
class TrigCondition(IntEnum):
    """
    Trig conditions for conditional triggering and probability.

    Used with Step.condition to control when a step fires.

    Categories:
    - Logic conditions (FILL, PRE, NEI, FIRST)
    - Probability conditions (PERCENT_*)
    - Pattern loop conditions (TX_RY = trigger on loop X, reset every Y loops)
    """
    NONE = 0
    FILL = 1
    NOT_FILL = 2
    PRE = 3
    NOT_PRE = 4
    NEI = 5
    NOT_NEI = 6
    FIRST = 7
    NOT_FIRST = 8
    # Probability conditions
    PERCENT_1 = 9
    PERCENT_2 = 10
    PERCENT_4 = 11
    PERCENT_6 = 12
    PERCENT_9 = 13
    PERCENT_13 = 14
    PERCENT_19 = 15
    PERCENT_25 = 16
    PERCENT_33 = 17
    PERCENT_41 = 18
    PERCENT_50 = 19
    PERCENT_59 = 20
    PERCENT_67 = 21
    PERCENT_75 = 22
    PERCENT_81 = 23
    PERCENT_87 = 24
    PERCENT_91 = 25
    PERCENT_94 = 26
    PERCENT_96 = 27
    PERCENT_98 = 28
    PERCENT_99 = 29
    # Pattern loop conditions (X:Y means trigger on loop X, reset every Y loops)
    T1_R2 = 30
    T2_R2 = 31
    T1_R3 = 32
    T2_R3 = 33
    T3_R3 = 34
    T1_R4 = 35
    T2_R4 = 36
    T3_R4 = 37
    T4_R4 = 38
    T1_R5 = 39
    T2_R5 = 40
    T3_R5 = 41
    T4_R5 = 42
    T5_R5 = 43
    T1_R6 = 44
    T2_R6 = 45
    T3_R6 = 46
    T4_R6 = 47
    T5_R6 = 48
    T6_R6 = 49
    T1_R7 = 50
    T2_R7 = 51
    T3_R7 = 52
    T4_R7 = 53
    T5_R7 = 54
    T6_R7 = 55
    T7_R7 = 56
    T1_R8 = 57
    T2_R8 = 58
    T3_R8 = 59
    T4_R8 = 60
    T5_R8 = 61
    T6_R8 = 62
    T7_R8 = 63
    T8_R8 = 64


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
