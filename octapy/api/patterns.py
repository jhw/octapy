"""
Pattern data structures for Octatrack banks.

A Pattern contains trig data for 8 audio tracks and 8 MIDI tracks,
plus scale/tempo settings and part assignment.

Each bank has 16 patterns.

Key offsets (from reverse engineering):
- Pattern size: 0x8EEC (36588) bytes
- Audio track size: 0x922 (2338) bytes per track
- Trig masks start at offset 0x09 within each track (after header)

Ported from ot-tools-io (Rust).
"""

from enum import IntEnum
from typing import List, Optional, Union

from . import OTBlock


# Pattern and track sizes (verified from gist)
PATTERN_SIZE = 0x8EEC           # 36588 bytes per pattern
AUDIO_TRACK_SIZE = 0x922        # 2338 bytes per audio track
MIDI_TRACK_SIZE = 0x4AC         # 1196 bytes per MIDI track (approximate)

# Headers
PATTERN_HEADER = bytes([0x50, 0x54, 0x52, 0x4E, 0x00, 0x00, 0x00, 0x00])  # "PTRN...."
AUDIO_TRACK_HEADER = bytes([0x54, 0x52, 0x41, 0x43])  # "TRAC"
MIDI_TRACK_HEADER = bytes([0x4D, 0x54, 0x52, 0x41])   # "MTRA"


class AudioTrackOffset(IntEnum):
    """Offsets within an audio track block (relative to track start)."""
    HEADER = 0                  # 4 bytes: "TRAC"
    UNKNOWN_1 = 4               # 4 bytes
    TRACK_ID = 8                # 1 byte: track number (0-7)
    TRIG_TRIGGER = 9            # 8 bytes: trigger trig masks
    TRIG_TRIGLESS = 17          # 8 bytes: trigless trig masks
    TRIG_PLOCK = 25             # 8 bytes: parameter lock trig masks
    TRIG_ONESHOT = 33           # 8 bytes: oneshot/hold trig masks
    TRIG_RECORDER = 41          # 32 bytes: recorder trig masks
    TRIG_SWING = 73             # 8 bytes: swing trig masks
    TRIG_SLIDE = 81             # 8 bytes: slide trig masks
    PER_TRACK_LEN = 89          # 1 byte: track length in per-track mode
    PER_TRACK_SCALE = 90        # 1 byte: track scale in per-track mode
    SWING_AMOUNT = 91           # 1 byte: swing amount (0-30)
    START_SILENT = 92           # 1 byte: start silent setting
    PLAYS_FREE = 93             # 1 byte: plays free setting
    TRIG_MODE = 94              # 1 byte: trig mode
    TRIG_QUANT = 95             # 1 byte: trig quantization
    ONESHOT_TRK = 96            # 1 byte: oneshot track setting
    UNKNOWN_2 = 97              # 1 byte
    PLOCKS = 98                 # 2048 bytes: 32 bytes × 64 steps
    UNKNOWN_3 = 2146            # 64 bytes
    TRIG_CONDITIONS = 2210      # 128 bytes: 2 bytes × 64 steps


# P-lock constants
PLOCK_SIZE = 32                 # Bytes per step's parameter locks
PLOCK_DISABLED = 255            # Value indicating p-lock is disabled


class PlockOffset(IntEnum):
    """
    Offsets within a single step's parameter lock data (32 bytes).

    SRC page (0-5): Meaning depends on machine type - use machine-specific methods.
    LFO page (6-11): Consistent across all machine types.
    AMP page (12-17): Consistent across all machine types.
    FX1 page (18-23): Meaning depends on selected effect.
    FX2 page (24-29): Meaning depends on selected effect.
    """
    # SRC/Machine page (6 bytes) - interpretation varies by machine type:
    #   Flex/Static: PTCH, STRT, LEN, RATE, RTRG, RTIM
    #   Thru: IN_AB, VOL_AB, unused, IN_CD, VOL_CD, unused
    #   Neighbor: all unused
    #   Pickup: PTCH, DIR, LEN, unused, GAIN, OP
    SRC_1 = 0
    SRC_2 = 1
    SRC_3 = 2
    SRC_4 = 3
    SRC_5 = 4
    SRC_6 = 5
    # LFO page (6 bytes) - consistent
    LFO_SPEED1 = 6
    LFO_SPEED2 = 7
    LFO_SPEED3 = 8
    LFO_DEPTH1 = 9
    LFO_DEPTH2 = 10
    LFO_DEPTH3 = 11
    # AMP page (6 bytes) - consistent
    AMP_ATTACK = 12
    AMP_HOLD = 13
    AMP_RELEASE = 14
    AMP_VOLUME = 15
    AMP_BALANCE = 16
    AMP_F = 17                  # Reserved param for Scenes/LFOs
    # FX1 page (6 bytes) - meaning depends on selected effect
    FX1_1 = 18
    FX1_2 = 19
    FX1_3 = 20
    FX1_4 = 21
    FX1_5 = 22
    FX1_6 = 23
    # FX2 page (6 bytes) - meaning depends on selected effect
    FX2_1 = 24
    FX2_2 = 25
    FX2_3 = 26
    FX2_4 = 27
    FX2_5 = 28
    FX2_6 = 29
    # Sample slot locks
    STATIC_SLOT = 30
    FLEX_SLOT = 31


class TrigCondition(IntEnum):
    """Trig conditions for conditional triggering and probability."""
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


class PatternOffset(IntEnum):
    """Offsets within a pattern block (relative to pattern start)."""
    HEADER = 0                  # 8 bytes: "PTRN...."
    AUDIO_TRACKS = 8            # 8 audio tracks, each AUDIO_TRACK_SIZE bytes
    # MIDI tracks follow audio tracks
    # Scale/settings at end of pattern
    # TODO: Verify these offsets with actual OT files
    SCALE_LENGTH = 36577        # 1 byte: pattern length (16 = 16 steps)
    SCALE_MULT = 36578          # 1 byte: scale multiplier
    PART_ASSIGNMENT = 36581     # 1 byte: assigned part (0-3 = Part 1-4)


class AudioTrack(OTBlock):
    """
    Trig data for a single audio track within a pattern.

    Contains trig masks (which steps have triggers) and track settings.
    """

    BLOCK_SIZE = AUDIO_TRACK_SIZE

    def __init__(self, track_id: int = 0):
        super().__init__()
        self._data = bytearray(AUDIO_TRACK_SIZE)

        # Set header
        self._data[0:4] = AUDIO_TRACK_HEADER

        # Set track ID
        self._data[AudioTrackOffset.TRACK_ID] = track_id

        # Set default swing pattern (alternating steps)
        for i in range(8):
            self._data[AudioTrackOffset.TRIG_SWING + i] = 170  # 0b10101010

        # Set default per-track settings
        self._data[AudioTrackOffset.PER_TRACK_LEN] = 16
        self._data[AudioTrackOffset.PER_TRACK_SCALE] = 2  # 1x

        # Set default pattern settings
        self._data[AudioTrackOffset.START_SILENT] = 255

    @property
    def track_id(self) -> int:
        """Get the track ID (0-7)."""
        return self._data[AudioTrackOffset.TRACK_ID]

    def get_trigger_steps(self) -> List[int]:
        """
        Get list of steps (1-64) that have trigger trigs.

        Returns:
            List of step numbers (1-64) with triggers
        """
        return self._trig_mask_to_steps(AudioTrackOffset.TRIG_TRIGGER)

    def set_trigger_steps(self, steps: List[int]):
        """
        Set which steps (1-64) have trigger trigs.

        Args:
            steps: List of step numbers (1-64) to set as triggers
        """
        self._steps_to_trig_mask(steps, AudioTrackOffset.TRIG_TRIGGER)

    def get_trigless_steps(self) -> List[int]:
        """Get list of steps with trigless (envelope) trigs."""
        return self._trig_mask_to_steps(AudioTrackOffset.TRIG_TRIGLESS)

    def set_trigless_steps(self, steps: List[int]):
        """Set which steps have trigless trigs."""
        self._steps_to_trig_mask(steps, AudioTrackOffset.TRIG_TRIGLESS)

    def _trig_mask_to_steps(self, offset: int) -> List[int]:
        """
        Convert 8-byte trig mask to list of step numbers.

        The mask layout is:
        - Bytes 0-1: Page 4 (steps 49-64)
        - Bytes 2-3: Page 3 (steps 33-48)
        - Bytes 4-5: Page 2 (steps 17-32)
        - Bytes 6-7: Page 1 (steps 1-16) - reversed order
        """
        steps = []

        # Page 1 (bytes 6-7, reversed: byte 7 = steps 1-8, byte 6 = steps 9-16)
        for bit in range(8):
            if self._data[offset + 7] & (1 << bit):
                steps.append(bit + 1)
        for bit in range(8):
            if self._data[offset + 6] & (1 << bit):
                steps.append(bit + 9)

        # Page 2 (bytes 4-5)
        for bit in range(8):
            if self._data[offset + 4] & (1 << bit):
                steps.append(bit + 17)
        for bit in range(8):
            if self._data[offset + 5] & (1 << bit):
                steps.append(bit + 25)

        # Page 3 (bytes 2-3)
        for bit in range(8):
            if self._data[offset + 2] & (1 << bit):
                steps.append(bit + 33)
        for bit in range(8):
            if self._data[offset + 3] & (1 << bit):
                steps.append(bit + 41)

        # Page 4 (bytes 0-1)
        for bit in range(8):
            if self._data[offset + 0] & (1 << bit):
                steps.append(bit + 49)
        for bit in range(8):
            if self._data[offset + 1] & (1 << bit):
                steps.append(bit + 57)

        return sorted(steps)

    def _steps_to_trig_mask(self, steps: List[int], offset: int):
        """Convert list of step numbers to 8-byte trig mask."""
        # Clear existing mask
        for i in range(8):
            self._data[offset + i] = 0

        for step in steps:
            if step < 1 or step > 64:
                continue

            if step <= 8:
                self._data[offset + 7] |= (1 << (step - 1))
            elif step <= 16:
                self._data[offset + 6] |= (1 << (step - 9))
            elif step <= 24:
                self._data[offset + 4] |= (1 << (step - 17))
            elif step <= 32:
                self._data[offset + 5] |= (1 << (step - 25))
            elif step <= 40:
                self._data[offset + 2] |= (1 << (step - 33))
            elif step <= 48:
                self._data[offset + 3] |= (1 << (step - 41))
            elif step <= 56:
                self._data[offset + 0] |= (1 << (step - 49))
            else:
                self._data[offset + 1] |= (1 << (step - 57))

    def check_header(self) -> bool:
        """Verify the header matches expected audio track header."""
        return bytes(self._data[0:4]) == AUDIO_TRACK_HEADER

    # =========================================================================
    # P-Lock (Parameter Lock) Methods - Core
    # =========================================================================

    def _get_plock_offset(self, step: int, param: Union[PlockOffset, int]) -> int:
        """Get the byte offset for a p-lock parameter at a given step."""
        if step < 1 or step > 64:
            raise ValueError(f"Step must be 1-64, got {step}")
        return AudioTrackOffset.PLOCKS + (step - 1) * PLOCK_SIZE + int(param)

    def _get_plock(self, step: int, param: Union[PlockOffset, int]) -> Optional[int]:
        """Get a p-lock value. Returns None if disabled (255)."""
        offset = self._get_plock_offset(step, param)
        value = self._data[offset]
        return None if value == PLOCK_DISABLED else value

    def _set_plock(self, step: int, param: Union[PlockOffset, int], value: Optional[int]):
        """Set a p-lock value. None disables the p-lock."""
        offset = self._get_plock_offset(step, param)
        if value is None:
            self._data[offset] = PLOCK_DISABLED
        else:
            self._data[offset] = value & 0x7F  # Clamp to 0-127

    # =========================================================================
    # SRC Page - Flex/Static Machine Methods
    # =========================================================================

    def get_flex_pitch(self, step: int) -> Optional[int]:
        """Get pitch p-lock for Flex/Static machine (SRC param 1)."""
        return self._get_plock(step, PlockOffset.SRC_1)

    def set_flex_pitch(self, step: int, value: Optional[int]):
        """Set pitch p-lock for Flex/Static machine (SRC param 1)."""
        self._set_plock(step, PlockOffset.SRC_1, value)

    def get_flex_start(self, step: int) -> Optional[int]:
        """Get sample start p-lock for Flex/Static machine (SRC param 2)."""
        return self._get_plock(step, PlockOffset.SRC_2)

    def set_flex_start(self, step: int, value: Optional[int]):
        """Set sample start p-lock for Flex/Static machine (SRC param 2)."""
        self._set_plock(step, PlockOffset.SRC_2, value)

    def get_flex_length(self, step: int) -> Optional[int]:
        """Get sample length p-lock for Flex/Static machine (SRC param 3)."""
        return self._get_plock(step, PlockOffset.SRC_3)

    def set_flex_length(self, step: int, value: Optional[int]):
        """Set sample length p-lock for Flex/Static machine (SRC param 3)."""
        self._set_plock(step, PlockOffset.SRC_3, value)

    def get_flex_rate(self, step: int) -> Optional[int]:
        """Get playback rate p-lock for Flex/Static machine (SRC param 4).
        127 = normal forward, <64 = reverse."""
        return self._get_plock(step, PlockOffset.SRC_4)

    def set_flex_rate(self, step: int, value: Optional[int]):
        """Set playback rate p-lock for Flex/Static machine (SRC param 4).
        127 = normal forward, <64 = reverse."""
        self._set_plock(step, PlockOffset.SRC_4, value)

    def get_flex_retrig(self, step: int) -> Optional[int]:
        """Get retrig count p-lock for Flex/Static machine (SRC param 5)."""
        return self._get_plock(step, PlockOffset.SRC_5)

    def set_flex_retrig(self, step: int, value: Optional[int]):
        """Set retrig count p-lock for Flex/Static machine (SRC param 5)."""
        self._set_plock(step, PlockOffset.SRC_5, value)

    def get_flex_retrig_time(self, step: int) -> Optional[int]:
        """Get retrig time p-lock for Flex/Static machine (SRC param 6)."""
        return self._get_plock(step, PlockOffset.SRC_6)

    def set_flex_retrig_time(self, step: int, value: Optional[int]):
        """Set retrig time p-lock for Flex/Static machine (SRC param 6)."""
        self._set_plock(step, PlockOffset.SRC_6, value)

    # =========================================================================
    # SRC Page - Thru Machine Methods
    # =========================================================================

    def get_thru_in_ab(self, step: int) -> Optional[int]:
        """Get input A/B select p-lock for Thru machine (SRC param 1)."""
        return self._get_plock(step, PlockOffset.SRC_1)

    def set_thru_in_ab(self, step: int, value: Optional[int]):
        """Set input A/B select p-lock for Thru machine (SRC param 1)."""
        self._set_plock(step, PlockOffset.SRC_1, value)

    def get_thru_vol_ab(self, step: int) -> Optional[int]:
        """Get volume A/B p-lock for Thru machine (SRC param 2)."""
        return self._get_plock(step, PlockOffset.SRC_2)

    def set_thru_vol_ab(self, step: int, value: Optional[int]):
        """Set volume A/B p-lock for Thru machine (SRC param 2)."""
        self._set_plock(step, PlockOffset.SRC_2, value)

    def get_thru_in_cd(self, step: int) -> Optional[int]:
        """Get input C/D select p-lock for Thru machine (SRC param 4)."""
        return self._get_plock(step, PlockOffset.SRC_4)

    def set_thru_in_cd(self, step: int, value: Optional[int]):
        """Set input C/D select p-lock for Thru machine (SRC param 4)."""
        self._set_plock(step, PlockOffset.SRC_4, value)

    def get_thru_vol_cd(self, step: int) -> Optional[int]:
        """Get volume C/D p-lock for Thru machine (SRC param 5)."""
        return self._get_plock(step, PlockOffset.SRC_5)

    def set_thru_vol_cd(self, step: int, value: Optional[int]):
        """Set volume C/D p-lock for Thru machine (SRC param 5)."""
        self._set_plock(step, PlockOffset.SRC_5, value)

    # =========================================================================
    # SRC Page - Neighbor Machine Methods
    # =========================================================================

    def get_neighbor_1(self, step: int) -> Optional[int]:
        """Get p-lock for Neighbor machine (SRC param 1). Unused on Neighbor."""
        return self._get_plock(step, PlockOffset.SRC_1)

    def set_neighbor_1(self, step: int, value: Optional[int]):
        """Set p-lock for Neighbor machine (SRC param 1). Unused on Neighbor."""
        self._set_plock(step, PlockOffset.SRC_1, value)

    def get_neighbor_2(self, step: int) -> Optional[int]:
        """Get p-lock for Neighbor machine (SRC param 2). Unused on Neighbor."""
        return self._get_plock(step, PlockOffset.SRC_2)

    def set_neighbor_2(self, step: int, value: Optional[int]):
        """Set p-lock for Neighbor machine (SRC param 2). Unused on Neighbor."""
        self._set_plock(step, PlockOffset.SRC_2, value)

    def get_neighbor_3(self, step: int) -> Optional[int]:
        """Get p-lock for Neighbor machine (SRC param 3). Unused on Neighbor."""
        return self._get_plock(step, PlockOffset.SRC_3)

    def set_neighbor_3(self, step: int, value: Optional[int]):
        """Set p-lock for Neighbor machine (SRC param 3). Unused on Neighbor."""
        self._set_plock(step, PlockOffset.SRC_3, value)

    def get_neighbor_4(self, step: int) -> Optional[int]:
        """Get p-lock for Neighbor machine (SRC param 4). Unused on Neighbor."""
        return self._get_plock(step, PlockOffset.SRC_4)

    def set_neighbor_4(self, step: int, value: Optional[int]):
        """Set p-lock for Neighbor machine (SRC param 4). Unused on Neighbor."""
        self._set_plock(step, PlockOffset.SRC_4, value)

    def get_neighbor_5(self, step: int) -> Optional[int]:
        """Get p-lock for Neighbor machine (SRC param 5). Unused on Neighbor."""
        return self._get_plock(step, PlockOffset.SRC_5)

    def set_neighbor_5(self, step: int, value: Optional[int]):
        """Set p-lock for Neighbor machine (SRC param 5). Unused on Neighbor."""
        self._set_plock(step, PlockOffset.SRC_5, value)

    def get_neighbor_6(self, step: int) -> Optional[int]:
        """Get p-lock for Neighbor machine (SRC param 6). Unused on Neighbor."""
        return self._get_plock(step, PlockOffset.SRC_6)

    def set_neighbor_6(self, step: int, value: Optional[int]):
        """Set p-lock for Neighbor machine (SRC param 6). Unused on Neighbor."""
        self._set_plock(step, PlockOffset.SRC_6, value)

    # =========================================================================
    # SRC Page - Pickup Machine Methods
    # =========================================================================

    def get_pickup_pitch(self, step: int) -> Optional[int]:
        """Get pitch p-lock for Pickup machine (SRC param 1)."""
        return self._get_plock(step, PlockOffset.SRC_1)

    def set_pickup_pitch(self, step: int, value: Optional[int]):
        """Set pitch p-lock for Pickup machine (SRC param 1)."""
        self._set_plock(step, PlockOffset.SRC_1, value)

    def get_pickup_dir(self, step: int) -> Optional[int]:
        """Get direction p-lock for Pickup machine (SRC param 2)."""
        return self._get_plock(step, PlockOffset.SRC_2)

    def set_pickup_dir(self, step: int, value: Optional[int]):
        """Set direction p-lock for Pickup machine (SRC param 2)."""
        self._set_plock(step, PlockOffset.SRC_2, value)

    def get_pickup_length(self, step: int) -> Optional[int]:
        """Get length p-lock for Pickup machine (SRC param 3)."""
        return self._get_plock(step, PlockOffset.SRC_3)

    def set_pickup_length(self, step: int, value: Optional[int]):
        """Set length p-lock for Pickup machine (SRC param 3)."""
        self._set_plock(step, PlockOffset.SRC_3, value)

    def get_pickup_gain(self, step: int) -> Optional[int]:
        """Get gain p-lock for Pickup machine (SRC param 5)."""
        return self._get_plock(step, PlockOffset.SRC_5)

    def set_pickup_gain(self, step: int, value: Optional[int]):
        """Set gain p-lock for Pickup machine (SRC param 5)."""
        self._set_plock(step, PlockOffset.SRC_5, value)

    def get_pickup_op(self, step: int) -> Optional[int]:
        """Get operation mode p-lock for Pickup machine (SRC param 6)."""
        return self._get_plock(step, PlockOffset.SRC_6)

    def set_pickup_op(self, step: int, value: Optional[int]):
        """Set operation mode p-lock for Pickup machine (SRC param 6)."""
        self._set_plock(step, PlockOffset.SRC_6, value)

    # =========================================================================
    # LFO Page Methods
    # =========================================================================

    def get_lfo_speed1(self, step: int) -> Optional[int]:
        """Get LFO 1 speed p-lock."""
        return self._get_plock(step, PlockOffset.LFO_SPEED1)

    def set_lfo_speed1(self, step: int, value: Optional[int]):
        """Set LFO 1 speed p-lock."""
        self._set_plock(step, PlockOffset.LFO_SPEED1, value)

    def get_lfo_speed2(self, step: int) -> Optional[int]:
        """Get LFO 2 speed p-lock."""
        return self._get_plock(step, PlockOffset.LFO_SPEED2)

    def set_lfo_speed2(self, step: int, value: Optional[int]):
        """Set LFO 2 speed p-lock."""
        self._set_plock(step, PlockOffset.LFO_SPEED2, value)

    def get_lfo_speed3(self, step: int) -> Optional[int]:
        """Get LFO 3 speed p-lock."""
        return self._get_plock(step, PlockOffset.LFO_SPEED3)

    def set_lfo_speed3(self, step: int, value: Optional[int]):
        """Set LFO 3 speed p-lock."""
        self._set_plock(step, PlockOffset.LFO_SPEED3, value)

    def get_lfo_depth1(self, step: int) -> Optional[int]:
        """Get LFO 1 depth p-lock."""
        return self._get_plock(step, PlockOffset.LFO_DEPTH1)

    def set_lfo_depth1(self, step: int, value: Optional[int]):
        """Set LFO 1 depth p-lock."""
        self._set_plock(step, PlockOffset.LFO_DEPTH1, value)

    def get_lfo_depth2(self, step: int) -> Optional[int]:
        """Get LFO 2 depth p-lock."""
        return self._get_plock(step, PlockOffset.LFO_DEPTH2)

    def set_lfo_depth2(self, step: int, value: Optional[int]):
        """Set LFO 2 depth p-lock."""
        self._set_plock(step, PlockOffset.LFO_DEPTH2, value)

    def get_lfo_depth3(self, step: int) -> Optional[int]:
        """Get LFO 3 depth p-lock."""
        return self._get_plock(step, PlockOffset.LFO_DEPTH3)

    def set_lfo_depth3(self, step: int, value: Optional[int]):
        """Set LFO 3 depth p-lock."""
        self._set_plock(step, PlockOffset.LFO_DEPTH3, value)

    # =========================================================================
    # AMP Page Methods
    # =========================================================================

    def get_amp_attack(self, step: int) -> Optional[int]:
        """Get attack p-lock."""
        return self._get_plock(step, PlockOffset.AMP_ATTACK)

    def set_amp_attack(self, step: int, value: Optional[int]):
        """Set attack p-lock."""
        self._set_plock(step, PlockOffset.AMP_ATTACK, value)

    def get_amp_hold(self, step: int) -> Optional[int]:
        """Get hold p-lock."""
        return self._get_plock(step, PlockOffset.AMP_HOLD)

    def set_amp_hold(self, step: int, value: Optional[int]):
        """Set hold p-lock."""
        self._set_plock(step, PlockOffset.AMP_HOLD, value)

    def get_amp_release(self, step: int) -> Optional[int]:
        """Get release p-lock."""
        return self._get_plock(step, PlockOffset.AMP_RELEASE)

    def set_amp_release(self, step: int, value: Optional[int]):
        """Set release p-lock."""
        self._set_plock(step, PlockOffset.AMP_RELEASE, value)

    def get_amp_volume(self, step: int) -> Optional[int]:
        """Get volume p-lock."""
        return self._get_plock(step, PlockOffset.AMP_VOLUME)

    def set_amp_volume(self, step: int, value: Optional[int]):
        """Set volume p-lock."""
        self._set_plock(step, PlockOffset.AMP_VOLUME, value)

    def get_amp_balance(self, step: int) -> Optional[int]:
        """Get balance p-lock."""
        return self._get_plock(step, PlockOffset.AMP_BALANCE)

    def set_amp_balance(self, step: int, value: Optional[int]):
        """Set balance p-lock."""
        self._set_plock(step, PlockOffset.AMP_BALANCE, value)

    def get_amp_f(self, step: int) -> Optional[int]:
        """Get AMP F parameter p-lock (reserved for Scenes/LFOs)."""
        return self._get_plock(step, PlockOffset.AMP_F)

    def set_amp_f(self, step: int, value: Optional[int]):
        """Set AMP F parameter p-lock (reserved for Scenes/LFOs)."""
        self._set_plock(step, PlockOffset.AMP_F, value)

    # Convenience aliases for common usage
    def get_volume(self, step: int) -> Optional[int]:
        """Alias for get_amp_volume."""
        return self.get_amp_volume(step)

    def set_volume(self, step: int, value: Optional[int]):
        """Alias for set_amp_volume."""
        self.set_amp_volume(step, value)

    # =========================================================================
    # FX1 Page Methods (generic - meaning depends on selected effect)
    # =========================================================================

    def get_fx1_1(self, step: int) -> Optional[int]:
        """Get FX1 param 1 p-lock."""
        return self._get_plock(step, PlockOffset.FX1_1)

    def set_fx1_1(self, step: int, value: Optional[int]):
        """Set FX1 param 1 p-lock."""
        self._set_plock(step, PlockOffset.FX1_1, value)

    def get_fx1_2(self, step: int) -> Optional[int]:
        """Get FX1 param 2 p-lock."""
        return self._get_plock(step, PlockOffset.FX1_2)

    def set_fx1_2(self, step: int, value: Optional[int]):
        """Set FX1 param 2 p-lock."""
        self._set_plock(step, PlockOffset.FX1_2, value)

    def get_fx1_3(self, step: int) -> Optional[int]:
        """Get FX1 param 3 p-lock."""
        return self._get_plock(step, PlockOffset.FX1_3)

    def set_fx1_3(self, step: int, value: Optional[int]):
        """Set FX1 param 3 p-lock."""
        self._set_plock(step, PlockOffset.FX1_3, value)

    def get_fx1_4(self, step: int) -> Optional[int]:
        """Get FX1 param 4 p-lock."""
        return self._get_plock(step, PlockOffset.FX1_4)

    def set_fx1_4(self, step: int, value: Optional[int]):
        """Set FX1 param 4 p-lock."""
        self._set_plock(step, PlockOffset.FX1_4, value)

    def get_fx1_5(self, step: int) -> Optional[int]:
        """Get FX1 param 5 p-lock."""
        return self._get_plock(step, PlockOffset.FX1_5)

    def set_fx1_5(self, step: int, value: Optional[int]):
        """Set FX1 param 5 p-lock."""
        self._set_plock(step, PlockOffset.FX1_5, value)

    def get_fx1_6(self, step: int) -> Optional[int]:
        """Get FX1 param 6 p-lock."""
        return self._get_plock(step, PlockOffset.FX1_6)

    def set_fx1_6(self, step: int, value: Optional[int]):
        """Set FX1 param 6 p-lock."""
        self._set_plock(step, PlockOffset.FX1_6, value)

    # =========================================================================
    # FX2 Page Methods (generic - meaning depends on selected effect)
    # =========================================================================

    def get_fx2_1(self, step: int) -> Optional[int]:
        """Get FX2 param 1 p-lock."""
        return self._get_plock(step, PlockOffset.FX2_1)

    def set_fx2_1(self, step: int, value: Optional[int]):
        """Set FX2 param 1 p-lock."""
        self._set_plock(step, PlockOffset.FX2_1, value)

    def get_fx2_2(self, step: int) -> Optional[int]:
        """Get FX2 param 2 p-lock."""
        return self._get_plock(step, PlockOffset.FX2_2)

    def set_fx2_2(self, step: int, value: Optional[int]):
        """Set FX2 param 2 p-lock."""
        self._set_plock(step, PlockOffset.FX2_2, value)

    def get_fx2_3(self, step: int) -> Optional[int]:
        """Get FX2 param 3 p-lock."""
        return self._get_plock(step, PlockOffset.FX2_3)

    def set_fx2_3(self, step: int, value: Optional[int]):
        """Set FX2 param 3 p-lock."""
        self._set_plock(step, PlockOffset.FX2_3, value)

    def get_fx2_4(self, step: int) -> Optional[int]:
        """Get FX2 param 4 p-lock."""
        return self._get_plock(step, PlockOffset.FX2_4)

    def set_fx2_4(self, step: int, value: Optional[int]):
        """Set FX2 param 4 p-lock."""
        self._set_plock(step, PlockOffset.FX2_4, value)

    def get_fx2_5(self, step: int) -> Optional[int]:
        """Get FX2 param 5 p-lock."""
        return self._get_plock(step, PlockOffset.FX2_5)

    def set_fx2_5(self, step: int, value: Optional[int]):
        """Set FX2 param 5 p-lock."""
        self._set_plock(step, PlockOffset.FX2_5, value)

    def get_fx2_6(self, step: int) -> Optional[int]:
        """Get FX2 param 6 p-lock."""
        return self._get_plock(step, PlockOffset.FX2_6)

    def set_fx2_6(self, step: int, value: Optional[int]):
        """Set FX2 param 6 p-lock."""
        self._set_plock(step, PlockOffset.FX2_6, value)

    # =========================================================================
    # Sample Slot Lock Methods
    # =========================================================================

    def get_static_slot_lock(self, step: int) -> Optional[int]:
        """Get static sample slot lock for a step."""
        return self._get_plock(step, PlockOffset.STATIC_SLOT)

    def set_static_slot_lock(self, step: int, value: Optional[int]):
        """Set static sample slot lock for a step."""
        self._set_plock(step, PlockOffset.STATIC_SLOT, value)

    def get_flex_slot_lock(self, step: int) -> Optional[int]:
        """Get flex sample slot lock for a step."""
        return self._get_plock(step, PlockOffset.FLEX_SLOT)

    def set_flex_slot_lock(self, step: int, value: Optional[int]):
        """Set flex sample slot lock for a step."""
        self._set_plock(step, PlockOffset.FLEX_SLOT, value)

    # Legacy aliases for backward compatibility
    def get_pitch(self, step: int) -> Optional[int]:
        """Alias for get_flex_pitch (assumes Flex/Static machine)."""
        return self.get_flex_pitch(step)

    def set_pitch(self, step: int, value: Optional[int]):
        """Alias for set_flex_pitch (assumes Flex/Static machine)."""
        self.set_flex_pitch(step, value)

    # =========================================================================
    # Trig Condition Methods
    # =========================================================================

    def _get_trig_condition_offset(self, step: int) -> int:
        """Get the byte offset for trig condition data at a given step."""
        if step < 1 or step > 64:
            raise ValueError(f"Step must be 1-64, got {step}")
        # Each step has 2 bytes: [repeats+offset, condition+offset_flag]
        return AudioTrackOffset.TRIG_CONDITIONS + (step - 1) * 2

    def get_trig_condition(self, step: int) -> TrigCondition:
        """
        Get the trig condition for a step.

        Args:
            step: Step number (1-64)

        Returns:
            TrigCondition enum value
        """
        offset = self._get_trig_condition_offset(step)
        # Condition is in byte 1, masked by 128 (offset flag)
        raw_value = self._data[offset + 1]
        condition_value = raw_value % 128  # Remove offset flag if present
        try:
            return TrigCondition(condition_value)
        except ValueError:
            return TrigCondition.NONE

    def set_trig_condition(
        self, step: int, condition: Union[TrigCondition, int]
    ):
        """
        Set the trig condition for a step.

        Args:
            step: Step number (1-64)
            condition: TrigCondition enum or raw value (0-64)
        """
        offset = self._get_trig_condition_offset(step)
        if isinstance(condition, TrigCondition):
            condition_value = condition.value
        else:
            condition_value = condition & 0x7F  # Max 127

        # Preserve the offset flag (bit 7) if present
        current = self._data[offset + 1]
        offset_flag = current & 0x80
        self._data[offset + 1] = offset_flag | condition_value

    def get_trig_repeat(self, step: int) -> int:
        """
        Get the trig repeat count for a step.

        Args:
            step: Step number (1-64)

        Returns:
            Number of repeats (1-8, where 1 means no repeat)
        """
        offset = self._get_trig_condition_offset(step)
        raw_value = self._data[offset]
        # Repeat count is encoded as (count - 1) * 32, masked within 0-224 range
        # The offset portion uses values 0-31
        repeat_portion = (raw_value // 32)
        return repeat_portion + 1

    def set_trig_repeat(self, step: int, count: int):
        """
        Set the trig repeat count for a step.

        Args:
            step: Step number (1-64)
            count: Number of repeats (1-8)
        """
        if count < 1 or count > 8:
            raise ValueError(f"Repeat count must be 1-8, got {count}")

        offset = self._get_trig_condition_offset(step)
        current = self._data[offset]
        # Preserve offset portion (0-31)
        offset_portion = current % 32
        repeat_portion = (count - 1) * 32
        self._data[offset] = offset_portion + repeat_portion


class Pattern(OTBlock):
    """
    An Octatrack Pattern containing trig data for all tracks.

    Provides access to audio tracks and pattern-level settings.
    """

    BLOCK_SIZE = PATTERN_SIZE

    def __init__(self):
        super().__init__()
        self._data = bytearray(PATTERN_SIZE)

        # Set header
        self._data[0:8] = PATTERN_HEADER

        # Initialize audio track headers
        for i in range(8):
            track_offset = PatternOffset.AUDIO_TRACKS + i * AUDIO_TRACK_SIZE
            self._data[track_offset:track_offset + 4] = AUDIO_TRACK_HEADER
            self._data[track_offset + AudioTrackOffset.TRACK_ID] = i

            # Set default swing
            for j in range(8):
                self._data[track_offset + AudioTrackOffset.TRIG_SWING + j] = 170

            # Set default per-track settings
            self._data[track_offset + AudioTrackOffset.PER_TRACK_LEN] = 16
            self._data[track_offset + AudioTrackOffset.PER_TRACK_SCALE] = 2
            self._data[track_offset + AudioTrackOffset.START_SILENT] = 255

    def get_audio_track(self, track: int) -> AudioTrack:
        """
        Get an AudioTrack view into this pattern's data.

        Args:
            track: Track number (1-8)

        Returns:
            AudioTrack instance backed by this pattern's buffer
        """
        offset = PatternOffset.AUDIO_TRACKS + (track - 1) * AUDIO_TRACK_SIZE
        track_data = self._data[offset:offset + AUDIO_TRACK_SIZE]

        audio_track = AudioTrack.__new__(AudioTrack)
        audio_track._data = bytearray(track_data)
        return audio_track

    def set_audio_track(self, track: int, audio_track: AudioTrack):
        """
        Copy an AudioTrack's data back into this pattern.

        Args:
            track: Track number (1-8)
            audio_track: AudioTrack with data to copy
        """
        offset = PatternOffset.AUDIO_TRACKS + (track - 1) * AUDIO_TRACK_SIZE
        self._data[offset:offset + AUDIO_TRACK_SIZE] = audio_track._data

    def set_trigger_steps(self, track: int, steps: List[int]):
        """
        Convenience method to set trigger steps for a track.

        Args:
            track: Track number (1-8)
            steps: List of step numbers (1-64)
        """
        audio_track = self.get_audio_track(track)
        audio_track.set_trigger_steps(steps)
        self.set_audio_track(track, audio_track)

    def get_trigger_steps(self, track: int) -> List[int]:
        """
        Convenience method to get trigger steps for a track.

        Args:
            track: Track number (1-8)

        Returns:
            List of step numbers (1-64)
        """
        return self.get_audio_track(track).get_trigger_steps()

    # =========================================================================
    # P-Lock Convenience Methods (Pattern-level, delegates to AudioTrack)
    # =========================================================================

    # --- AMP page ---
    def get_volume(self, track: int, step: int) -> Optional[int]:
        """Get volume p-lock for a track/step."""
        return self.get_audio_track(track).get_volume(step)

    def set_volume(self, track: int, step: int, value: Optional[int]):
        """Set volume p-lock for a track/step."""
        audio_track = self.get_audio_track(track)
        audio_track.set_volume(step, value)
        self.set_audio_track(track, audio_track)

    # --- Flex/Static machine SRC page ---
    def get_flex_pitch(self, track: int, step: int) -> Optional[int]:
        """Get pitch p-lock for Flex/Static machine."""
        return self.get_audio_track(track).get_flex_pitch(step)

    def set_flex_pitch(self, track: int, step: int, value: Optional[int]):
        """Set pitch p-lock for Flex/Static machine."""
        audio_track = self.get_audio_track(track)
        audio_track.set_flex_pitch(step, value)
        self.set_audio_track(track, audio_track)

    def get_flex_length(self, track: int, step: int) -> Optional[int]:
        """Get sample length p-lock for Flex/Static machine."""
        return self.get_audio_track(track).get_flex_length(step)

    def set_flex_length(self, track: int, step: int, value: Optional[int]):
        """Set sample length p-lock for Flex/Static machine."""
        audio_track = self.get_audio_track(track)
        audio_track.set_flex_length(step, value)
        self.set_audio_track(track, audio_track)

    def get_flex_rate(self, track: int, step: int) -> Optional[int]:
        """Get playback rate p-lock for Flex/Static machine."""
        return self.get_audio_track(track).get_flex_rate(step)

    def set_flex_rate(self, track: int, step: int, value: Optional[int]):
        """Set playback rate p-lock for Flex/Static machine."""
        audio_track = self.get_audio_track(track)
        audio_track.set_flex_rate(step, value)
        self.set_audio_track(track, audio_track)

    # Legacy alias
    def get_pitch(self, track: int, step: int) -> Optional[int]:
        """Alias for get_flex_pitch."""
        return self.get_flex_pitch(track, step)

    def set_pitch(self, track: int, step: int, value: Optional[int]):
        """Alias for set_flex_pitch."""
        self.set_flex_pitch(track, step, value)

    # --- Trig conditions ---
    def get_trig_condition(self, track: int, step: int) -> TrigCondition:
        """Get trig condition for a track/step."""
        return self.get_audio_track(track).get_trig_condition(step)

    def set_trig_condition(
        self, track: int, step: int, condition: Union[TrigCondition, int]
    ):
        """Set trig condition for a track/step."""
        audio_track = self.get_audio_track(track)
        audio_track.set_trig_condition(step, condition)
        self.set_audio_track(track, audio_track)

    def get_trig_repeat(self, track: int, step: int) -> int:
        """Get trig repeat count for a track/step."""
        return self.get_audio_track(track).get_trig_repeat(step)

    def set_trig_repeat(self, track: int, step: int, count: int):
        """Set trig repeat count for a track/step."""
        audio_track = self.get_audio_track(track)
        audio_track.set_trig_repeat(step, count)
        self.set_audio_track(track, audio_track)

    def check_header(self) -> bool:
        """Verify the header matches expected pattern header."""
        return bytes(self._data[0:8]) == PATTERN_HEADER

    # =========================================================================
    # Pattern Settings
    # =========================================================================

    @property
    def part_assignment(self) -> int:
        """
        Get the assigned part for this pattern (0-3 = Part 1-4).

        Returns:
            Part index (0-3)
        """
        return self._data[PatternOffset.PART_ASSIGNMENT]

    @part_assignment.setter
    def part_assignment(self, value: int):
        """
        Set the assigned part for this pattern.

        Args:
            value: Part index (0-3 = Part 1-4)
        """
        self._data[PatternOffset.PART_ASSIGNMENT] = value & 0x03


class PatternArray(list):
    """Collection of 16 patterns for a bank."""

    def __init__(self):
        super().__init__()
        for _ in range(16):
            self.append(Pattern())

    @classmethod
    def read(cls, data, patterns_offset: int):
        """
        Read 16 patterns from binary data.

        Args:
            data: Full bank data buffer
            patterns_offset: Offset to first pattern

        Returns:
            PatternArray instance
        """
        instance = cls.__new__(cls)
        list.__init__(instance)

        for i in range(16):
            start = patterns_offset + i * PATTERN_SIZE
            pattern_data = data[start:start + PATTERN_SIZE]

            pattern = Pattern.__new__(Pattern)
            pattern._data = bytearray(pattern_data)
            instance.append(pattern)

        return instance

    def write_to(self, data, patterns_offset: int):
        """
        Write 16 patterns back to binary data buffer.

        Args:
            data: Full bank data buffer (modified in place)
            patterns_offset: Offset to first pattern
        """
        for i, pattern in enumerate(self):
            start = patterns_offset + i * PATTERN_SIZE
            data[start:start + PATTERN_SIZE] = pattern._data
