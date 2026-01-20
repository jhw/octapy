"""
Pattern - standalone Pattern container with audio and MIDI tracks.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Bank binary data.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..._io import (
    PatternOffset,
    PATTERN_SIZE,
    AUDIO_TRACK_SIZE,
    MIDI_TRACK_PATTERN_SIZE,
)
from .audio_pattern_track import AudioPatternTrack
from .midi_pattern_track import MidiPatternTrack


class Pattern:
    """
    Pattern containing sequence data for all 8 audio and MIDI tracks.

    This is a standalone object that contains:
    - 8 AudioPatternTrack objects (audio step sequences)
    - 8 MidiPatternTrack objects (MIDI step sequences)
    - Pattern settings (part assignment, length, scale)

    Usage:
        # Create with constructor arguments
        pattern = Pattern(pattern_num=1, part=1)
        pattern.audio_track(1).active_steps = [1, 5, 9, 13]
        pattern.audio_track(1).step(5).volume = 100

        # Read from Bank binary (called by Bank)
        pattern = Pattern.read_from_bank(pattern_num, bank_data, pattern_offset)

        # Write to binary
        pattern.write_to_bank(bank_data, pattern_offset)
    """

    def __init__(
        self,
        pattern_num: int = 1,
        part: int = 1,
        scale_length: int = 16,
        scale_mult: int = 1,
        audio_tracks: Optional[List[AudioPatternTrack]] = None,
        midi_tracks: Optional[List[MidiPatternTrack]] = None,
    ):
        """
        Create a Pattern with optional configurations.

        Args:
            pattern_num: Pattern number (1-16)
            part: Assigned Part number (1-4)
            scale_length: Pattern length in steps (1-64, default 16)
            scale_mult: Scale multiplier (1-8)
            audio_tracks: Optional list of 8 AudioPatternTrack objects
            midi_tracks: Optional list of 8 MidiPatternTrack objects
        """
        self._pattern_num = pattern_num
        self._part = part
        self._scale_length = scale_length
        self._scale_mult = scale_mult

        # Initialize track collections
        self._audio_tracks: Dict[int, AudioPatternTrack] = {}
        self._midi_tracks: Dict[int, MidiPatternTrack] = {}

        # Create default audio tracks
        for i in range(1, 9):
            self._audio_tracks[i] = AudioPatternTrack(track_num=i)

        # Create default MIDI tracks
        for i in range(1, 9):
            self._midi_tracks[i] = MidiPatternTrack(track_num=i)

        # Apply provided tracks
        if audio_tracks:
            for track in audio_tracks:
                self._audio_tracks[track.track_num] = track

        if midi_tracks:
            for track in midi_tracks:
                self._midi_tracks[track.track_num] = track

    @classmethod
    def read_from_bank(cls, pattern_num: int, bank_data: bytes, pattern_offset: int = 0) -> "Pattern":
        """
        Read a Pattern from Bank binary data.

        Args:
            pattern_num: Pattern number (1-16)
            bank_data: Bank binary data
            pattern_offset: Offset to Pattern data in bank_data buffer

        Returns:
            Pattern instance
        """
        instance = cls.__new__(cls)
        instance._pattern_num = pattern_num

        # Read settings
        instance._scale_length = bank_data[pattern_offset + PatternOffset.SCALE_LENGTH]
        instance._scale_mult = bank_data[pattern_offset + PatternOffset.SCALE_MULT]
        instance._part = bank_data[pattern_offset + PatternOffset.PART_ASSIGNMENT] + 1

        # Read audio tracks
        instance._audio_tracks = {}
        audio_base = pattern_offset + PatternOffset.AUDIO_TRACKS
        for i in range(1, 9):
            track_offset = audio_base + (i - 1) * AUDIO_TRACK_SIZE
            track_data = bank_data[track_offset:track_offset + AUDIO_TRACK_SIZE]
            instance._audio_tracks[i] = AudioPatternTrack.read(i, track_data)

        # Read MIDI tracks
        instance._midi_tracks = {}
        midi_base = pattern_offset + PatternOffset.MIDI_TRACKS
        for i in range(1, 9):
            track_offset = midi_base + (i - 1) * MIDI_TRACK_PATTERN_SIZE
            track_data = bank_data[track_offset:track_offset + MIDI_TRACK_PATTERN_SIZE]
            instance._midi_tracks[i] = MidiPatternTrack.read(i, track_data)

        return instance

    def write_to_bank(self, bank_data: bytearray, pattern_offset: int = 0):
        """
        Write this Pattern to Bank binary data.

        Args:
            bank_data: Bank binary data (modified in place)
            pattern_offset: Offset to Pattern data in bank_data buffer
        """
        # Write settings
        bank_data[pattern_offset + PatternOffset.SCALE_LENGTH] = self._scale_length
        bank_data[pattern_offset + PatternOffset.SCALE_MULT] = self._scale_mult
        bank_data[pattern_offset + PatternOffset.PART_ASSIGNMENT] = (self._part - 1) & 0x03

        # Write audio tracks
        audio_base = pattern_offset + PatternOffset.AUDIO_TRACKS
        for i in range(1, 9):
            track_offset = audio_base + (i - 1) * AUDIO_TRACK_SIZE
            track_data = self._audio_tracks[i].write()
            bank_data[track_offset:track_offset + AUDIO_TRACK_SIZE] = track_data

        # Write MIDI tracks
        midi_base = pattern_offset + PatternOffset.MIDI_TRACKS
        for i in range(1, 9):
            track_offset = midi_base + (i - 1) * MIDI_TRACK_PATTERN_SIZE
            track_data = self._midi_tracks[i].write()
            bank_data[track_offset:track_offset + MIDI_TRACK_PATTERN_SIZE] = track_data

    def clone(self) -> "Pattern":
        """Create a copy of this Pattern with all tracks cloned."""
        instance = Pattern.__new__(Pattern)
        instance._pattern_num = self._pattern_num
        instance._part = self._part
        instance._scale_length = self._scale_length
        instance._scale_mult = self._scale_mult

        # Clone audio tracks
        instance._audio_tracks = {}
        for i, track in self._audio_tracks.items():
            instance._audio_tracks[i] = track.clone()

        # Clone MIDI tracks
        instance._midi_tracks = {}
        for i, track in self._midi_tracks.items():
            instance._midi_tracks[i] = track.clone()

        return instance

    # === Basic properties ===

    @property
    def pattern_num(self) -> int:
        """Get the pattern number (1-16)."""
        return self._pattern_num

    @property
    def part(self) -> int:
        """Get/set which Part this pattern uses (1-4)."""
        return self._part

    @part.setter
    def part(self, value: int):
        self._part = value

    @property
    def scale_length(self) -> int:
        """Get/set pattern length in steps (1-64)."""
        return self._scale_length

    @scale_length.setter
    def scale_length(self, value: int):
        self._scale_length = value

    @property
    def scale_mult(self) -> int:
        """Get/set scale multiplier (1-8)."""
        return self._scale_mult

    @scale_mult.setter
    def scale_mult(self, value: int):
        self._scale_mult = value

    # === Track access ===

    def audio_track(self, track_num: int) -> AudioPatternTrack:
        """
        Get audio pattern track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioPatternTrack instance
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        return self._audio_tracks[track_num]

    def set_audio_track(self, track_num: int, track: AudioPatternTrack):
        """
        Set audio pattern track at the given position.

        Args:
            track_num: Track number (1-8)
            track: AudioPatternTrack to set
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        track._track_num = track_num
        self._audio_tracks[track_num] = track

    def midi_track(self, track_num: int) -> MidiPatternTrack:
        """
        Get MIDI pattern track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPatternTrack instance
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        return self._midi_tracks[track_num]

    def set_midi_track(self, track_num: int, track: MidiPatternTrack):
        """
        Set MIDI pattern track at the given position.

        Args:
            track_num: Track number (1-8)
            track: MidiPatternTrack to set
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        track._track_num = track_num
        self._midi_tracks[track_num] = track

    # Alias for backward compatibility
    def track(self, track_num: int) -> AudioPatternTrack:
        """Alias for audio_track()."""
        return self.audio_track(track_num)

    # === Serialization ===

    def to_dict(self, include_steps: bool = False) -> dict:
        """
        Convert pattern to dictionary.

        Args:
            include_steps: Include step data in output (default False)

        Returns:
            Dict with pattern number, part assignment, audio and MIDI tracks.
        """
        return {
            "pattern": self._pattern_num,
            "part": self._part,
            "scale_length": self._scale_length,
            "scale_mult": self._scale_mult,
            "audio_tracks": [self._audio_tracks[n].to_dict(include_steps=include_steps) for n in range(1, 9)],
            "midi_tracks": [self._midi_tracks[n].to_dict(include_steps=include_steps) for n in range(1, 9)],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        """Create a Pattern from a dictionary."""
        pattern = cls(
            pattern_num=data.get("pattern", 1),
            part=data.get("part", 1),
            scale_length=data.get("scale_length", 16),
            scale_mult=data.get("scale_mult", 1),
        )

        if "audio_tracks" in data:
            for track_data in data["audio_tracks"]:
                track = AudioPatternTrack.from_dict(track_data)
                pattern._audio_tracks[track.track_num] = track

        if "midi_tracks" in data:
            for track_data in data["midi_tracks"]:
                track = MidiPatternTrack.from_dict(track_data)
                pattern._midi_tracks[track.track_num] = track

        return pattern

    def __eq__(self, other) -> bool:
        """Check equality based on all contained objects."""
        if not isinstance(other, Pattern):
            return NotImplemented
        if self._pattern_num != other._pattern_num:
            return False
        if self._part != other._part:
            return False
        if self._scale_length != other._scale_length:
            return False
        if self._scale_mult != other._scale_mult:
            return False
        if self._audio_tracks != other._audio_tracks:
            return False
        if self._midi_tracks != other._midi_tracks:
            return False
        return True

    def __repr__(self) -> str:
        return f"Pattern(pattern={self._pattern_num}, part={self._part}, length={self._scale_length})"
