"""
Enums for the Octatrack API.
"""

from enum import IntEnum


# === MIDI Notes ===

class MidiNote(IntEnum):
    """
    MIDI note values (0-127).

    Standard MIDI note mapping where C-1 = 0 and C4 = 60 (Middle C).
    This matches the Octatrack's display which shows notes starting at C-1.

    Naming convention:
    - Note name (C, D, E, F, G, A, B)
    - 's' suffix for sharps (Cs = C#, Ds = D#, etc.)
    - Octave number (-1 through 9, using _MINUS1 for -1 octave)

    Usage:
        midi_track.default_note = MidiNote.C4      # Middle C (60)
        midi_track.default_note = MidiNote.A4      # Concert pitch A (69)
        midi_track.default_note = MidiNote.C_MINUS1  # Lowest note (0)
    """
    # Octave -1 (notes 0-11)
    C_MINUS1 = 0
    Cs_MINUS1 = 1
    D_MINUS1 = 2
    Ds_MINUS1 = 3
    E_MINUS1 = 4
    F_MINUS1 = 5
    Fs_MINUS1 = 6
    G_MINUS1 = 7
    Gs_MINUS1 = 8
    A_MINUS1 = 9
    As_MINUS1 = 10
    B_MINUS1 = 11
    # Octave 0 (notes 12-23)
    C0 = 12
    Cs0 = 13
    D0 = 14
    Ds0 = 15
    E0 = 16
    F0 = 17
    Fs0 = 18
    G0 = 19
    Gs0 = 20
    A0 = 21
    As0 = 22
    B0 = 23
    # Octave 1 (notes 24-35)
    C1 = 24
    Cs1 = 25
    D1 = 26
    Ds1 = 27
    E1 = 28
    F1 = 29
    Fs1 = 30
    G1 = 31
    Gs1 = 32
    A1 = 33
    As1 = 34
    B1 = 35
    # Octave 2 (notes 36-47)
    C2 = 36
    Cs2 = 37
    D2 = 38
    Ds2 = 39
    E2 = 40
    F2 = 41
    Fs2 = 42
    G2 = 43
    Gs2 = 44
    A2 = 45
    As2 = 46
    B2 = 47
    # Octave 3 (notes 48-59)
    C3 = 48
    Cs3 = 49
    D3 = 50
    Ds3 = 51
    E3 = 52
    F3 = 53
    Fs3 = 54
    G3 = 55
    Gs3 = 56
    A3 = 57
    As3 = 58
    B3 = 59
    # Octave 4 (notes 60-71) - Middle C octave
    C4 = 60
    Cs4 = 61
    D4 = 62
    Ds4 = 63
    E4 = 64
    F4 = 65
    Fs4 = 66
    G4 = 67
    Gs4 = 68
    A4 = 69   # Concert pitch A (440 Hz)
    As4 = 70
    B4 = 71
    # Octave 5 (notes 72-83)
    C5 = 72
    Cs5 = 73
    D5 = 74
    Ds5 = 75
    E5 = 76
    F5 = 77
    Fs5 = 78
    G5 = 79
    Gs5 = 80
    A5 = 81
    As5 = 82
    B5 = 83
    # Octave 6 (notes 84-95)
    C6 = 84
    Cs6 = 85
    D6 = 86
    Ds6 = 87
    E6 = 88
    F6 = 89
    Fs6 = 90
    G6 = 91
    Gs6 = 92
    A6 = 93
    As6 = 94
    B6 = 95
    # Octave 7 (notes 96-107)
    C7 = 96
    Cs7 = 97
    D7 = 98
    Ds7 = 99
    E7 = 100
    F7 = 101
    Fs7 = 102
    G7 = 103
    Gs7 = 104
    A7 = 105
    As7 = 106
    B7 = 107
    # Octave 8 (notes 108-119)
    C8 = 108
    Cs8 = 109
    D8 = 110
    Ds8 = 111
    E8 = 112
    F8 = 113
    Fs8 = 114
    G8 = 115
    Gs8 = 116
    A8 = 117
    As8 = 118
    B8 = 119
    # Octave 9 (notes 120-127, incomplete octave)
    C9 = 120
    Cs9 = 121
    D9 = 122
    Ds9 = 123
    E9 = 124
    F9 = 125
    Fs9 = 126
    G9 = 127


# === Note length ===

class NoteLength(IntEnum):
    """
    Note length in musical subdivisions.

    Values are MIDI ticks at 24 PPQN (pulses per quarter note).
    These are the only values that map to clean musical fractions.

    Used for:
    - MIDI note length (default_length, arp_note_length)
    - Sample duration normalization (converted to ms based on BPM)

    At 120 BPM:
      - THIRTY_SECOND = 62.5ms (0.5 steps)
      - SIXTEENTH = 125ms (1 step)
      - EIGHTH = 250ms (2 steps)
      - QUARTER = 500ms (4 steps)
      - HALF = 1000ms (8 steps)
    """
    THIRTY_SECOND = 3   # 1/32 note
    SIXTEENTH = 6       # 1/16 note
    EIGHTH = 12         # 1/8 note
    QUARTER = 24        # 1/4 note
    HALF = 48           # 1/2 note


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


# === Sampler Setup Page (FUNC+SRC) ===

class LoopMode(IntEnum):
    """
    Loop mode for sampler machines (Flex/Static).

    Controls how the sample loops during playback.
    Set via FUNC+SRC page, encoder A (LOOP).

    Usage:
        track = part.flex_track(1)
        track.loop_mode = LoopMode.ON
    """
    OFF = 0    # No looping
    ON = 1     # Loop enabled
    PIPO = 2   # Ping-pong (alternating direction)
    AUTO = 3   # Use per-sample loop settings from audio editor


class SliceMode(IntEnum):
    """
    Slice mode for sampler machines (Flex/Static).

    When ON, the STRT parameter selects slices instead of linear position.
    Set via FUNC+SRC page, encoder B (SLIC).

    Usage:
        track = part.flex_track(1)
        track.slice_mode = SliceMode.ON
    """
    OFF = 0
    ON = 1


class LengthMode(IntEnum):
    """
    Length mode for sampler machines (Flex/Static).

    Controls how the LEN encoder on the main SRC page behaves.
    Set via FUNC+SRC page, encoder C (LEN).

    When SliceMode.OFF:
        - OFF: LEN encoder is inactive
        - TIME: LEN controls sample length linearly

    When SliceMode.ON:
        - SLICE: LEN controls number of slices to play
        - TIME: LEN controls slice length

    Usage:
        track = part.flex_track(1)
        track.length_mode = LengthMode.TIME  # Enable length control
    """
    OFF = 0    # LEN inactive (also SLICE when slice mode is ON)
    TIME = 1   # LEN controls length linearly


class RateMode(IntEnum):
    """
    Rate mode for sampler machines (Flex/Static).

    Controls whether the RATE encoder affects pitch or timestretch.
    Set via FUNC+SRC page, encoder D (RATE).

    Note: For reverse playback, use PITCH mode (timestretch cannot reverse).

    Usage:
        track = part.flex_track(1)
        track.rate_mode = RateMode.PITCH  # Allow reverse via negative rate
    """
    PITCH = 0  # RATE affects pitch (allows reverse with negative values)
    TSTR = 1   # RATE affects timestretch amount


class TimestretchMode(IntEnum):
    """
    Timestretch mode for sampler machines (Flex/Static) and Pickup.

    Controls the timestretch algorithm.
    Set via FUNC+SRC page, encoder E (TSTR).

    Usage:
        track = part.flex_track(1)
        track.timestretch_mode = TimestretchMode.OFF  # Disable for reverse playback
    """
    OFF = 0    # No timestretch
    AUTO = 1   # Use per-sample settings from audio editor
    NORM = 2   # Normal algorithm (smooth)
    BEAT = 3   # Beat-slicing algorithm (transient-aware)
