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
from typing import List

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


class PatternOffset(IntEnum):
    """Offsets within a pattern block (relative to pattern start)."""
    HEADER = 0                  # 8 bytes: "PTRN...."
    AUDIO_TRACKS = 8            # 8 audio tracks, each AUDIO_TRACK_SIZE bytes
    # MIDI tracks follow audio tracks
    # Scale settings at end of pattern


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

    def check_header(self) -> bool:
        """Verify the header matches expected pattern header."""
        return bytes(self._data[0:8]) == PATTERN_HEADER


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
