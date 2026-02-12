"""
AudioPatternTrack - standalone audio track sequence data for a Pattern.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Pattern binary data.
"""

from __future__ import annotations

from typing import List, Optional, Dict

from ...._io import (
    AudioTrackOffset,
    AUDIO_TRACK_SIZE,
    PLOCK_SIZE,
    NUM_STEPS,
    PLOCK_DISABLED,
)
from .._trig import _trig_mask_to_steps, _steps_to_trig_mask, _step_to_bit_position
from .step import AudioStep


class AudioPatternTrack:
    """
    Audio sequence data for a track within a Pattern.

    This is a standalone object that can be created with constructor arguments
    or read from Pattern binary data. It owns its data buffer and contains
    64 AudioStep objects.

    Provides access to 64 steps and their trigger states, p-locks, and conditions.

    Usage:
        # Create with constructor arguments
        track = AudioPatternTrack(
            track_num=1,
            active_steps=[1, 5, 9, 13],
        )

        # Access steps
        track.step(5).condition = TrigCondition.FILL
        track.step(5).volume = 100

        # Read from Pattern binary (called by Pattern)
        track = AudioPatternTrack.read(track_num, track_data)

        # Write to binary
        data = track.write()
    """

    def __init__(
        self,
        track_num: int = 1,
        active_steps: Optional[List[int]] = None,
        trigless_steps: Optional[List[int]] = None,
        length: int = 16,
        scale: int = 2,
    ):
        """
        Create an AudioPatternTrack with optional parameter overrides.

        Args:
            track_num: Track number (1-8)
            active_steps: List of active step numbers (1-64)
            trigless_steps: List of trigless step numbers (1-64)
            length: Track length in per-track mode (1-64, default 16)
            scale: Track scale in per-track mode (0-6, default 2=1x)
        """
        self._track_num = track_num
        self._data = bytearray(AUDIO_TRACK_SIZE)

        # Initialize header and track ID
        self._data[0:4] = b"TRAC"
        self._data[AudioTrackOffset.TRACK_ID] = track_num - 1

        # Initialize all p-locks to disabled
        for step_idx in range(NUM_STEPS):
            plock_offset = AudioTrackOffset.PLOCKS + step_idx * PLOCK_SIZE
            for i in range(PLOCK_SIZE):
                self._data[plock_offset + i] = PLOCK_DISABLED

        # Initialize per-track length and scale
        self._data[AudioTrackOffset.PER_TRACK_LEN] = length
        self._data[AudioTrackOffset.PER_TRACK_SCALE] = scale

        # Create step objects (lazy initialization)
        self._steps: Dict[int, AudioStep] = {}

        # Apply active/trigless steps
        if active_steps:
            self.active_steps = active_steps
        if trigless_steps:
            self.trigless_steps = trigless_steps

    @classmethod
    def read(cls, track_num: int, track_data: bytes) -> "AudioPatternTrack":
        """
        Read an AudioPatternTrack from binary data.

        Args:
            track_num: Track number (1-8)
            track_data: AUDIO_TRACK_SIZE bytes of track data

        Returns:
            AudioPatternTrack instance
        """
        instance = cls.__new__(cls)
        instance._track_num = track_num
        instance._data = bytearray(track_data[:AUDIO_TRACK_SIZE])
        instance._steps = {}
        return instance

    def write(self) -> bytes:
        """
        Write this AudioPatternTrack to binary data.

        Syncs any modified steps back to the buffer before returning.

        Returns:
            AUDIO_TRACK_SIZE bytes
        """
        # Sync any modified steps back to buffer
        for step_num, step in self._steps.items():
            self._sync_step_to_buffer(step_num, step)

        return bytes(self._data)

    def _sync_step_to_buffer(self, step_num: int, step: AudioStep):
        """Sync a step's data back to the track buffer."""
        step_idx = step_num - 1

        # Sync active bit
        byte_idx, bit_pos = _step_to_bit_position(step_num)
        offset = AudioTrackOffset.TRIG_TRIGGER + byte_idx
        if step.active:
            self._data[offset] |= (1 << bit_pos)
        else:
            self._data[offset] &= ~(1 << bit_pos)

        # Sync trigless bit
        offset = AudioTrackOffset.TRIG_TRIGLESS + byte_idx
        if step.trigless:
            self._data[offset] |= (1 << bit_pos)
        else:
            self._data[offset] &= ~(1 << bit_pos)

        # Sync condition data
        active, trigless, condition_data, plock_data = step.write()
        cond_offset = AudioTrackOffset.TRIG_CONDITIONS + step_idx * 2
        self._data[cond_offset:cond_offset + 2] = condition_data

        # Sync p-lock data
        plock_offset = AudioTrackOffset.PLOCKS + step_idx * PLOCK_SIZE
        self._data[plock_offset:plock_offset + PLOCK_SIZE] = plock_data

    def clone(self) -> "AudioPatternTrack":
        """Create a copy of this AudioPatternTrack."""
        instance = AudioPatternTrack.__new__(AudioPatternTrack)
        instance._track_num = self._track_num
        instance._data = bytearray(self._data)
        instance._steps = {}
        return instance

    # === Basic properties ===

    @property
    def track_num(self) -> int:
        """Get the track number (1-8)."""
        return self._track_num

    @property
    def length(self) -> int:
        """
        Get/set track length in per-track mode (1-64).

        Only applies when Pattern.scale_mode is ScaleMode.PER_TRACK.
        """
        return self._data[AudioTrackOffset.PER_TRACK_LEN]

    @length.setter
    def length(self, value: int):
        if not 1 <= value <= 64:
            raise ValueError(f"length must be 1-64, got {value}")
        self._data[AudioTrackOffset.PER_TRACK_LEN] = value

    @property
    def scale(self) -> int:
        """
        Get/set track scale in per-track mode.

        Only applies when Pattern.scale_mode is ScaleMode.PER_TRACK.

        Values: 0=2x, 1=3/2x, 2=1x (default), 3=3/4x, 4=1/2x, 5=1/4x, 6=1/8x
        """
        return self._data[AudioTrackOffset.PER_TRACK_SCALE]

    @scale.setter
    def scale(self, value: int):
        if not 0 <= value <= 6:
            raise ValueError(f"scale must be 0-6, got {value}")
        self._data[AudioTrackOffset.PER_TRACK_SCALE] = value

    # === Step access ===

    def step(self, step_num: int) -> AudioStep:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            AudioStep instance for this position
        """
        if step_num < 1 or step_num > 64:
            raise ValueError(f"Step number must be 1-64, got {step_num}")

        if step_num not in self._steps:
            self._steps[step_num] = self._load_step(step_num)

        return self._steps[step_num]

    def _load_step(self, step_num: int) -> AudioStep:
        """Load a step from the buffer and connect sync callback."""
        step_idx = step_num - 1

        # Get active bit
        byte_idx, bit_pos = _step_to_bit_position(step_num)
        active = bool(self._data[AudioTrackOffset.TRIG_TRIGGER + byte_idx] & (1 << bit_pos))

        # Get trigless bit
        trigless = bool(self._data[AudioTrackOffset.TRIG_TRIGLESS + byte_idx] & (1 << bit_pos))

        # Get condition data
        cond_offset = AudioTrackOffset.TRIG_CONDITIONS + step_idx * 2
        condition_data = bytes(self._data[cond_offset:cond_offset + 2])

        # Get p-lock data
        plock_offset = AudioTrackOffset.PLOCKS + step_idx * PLOCK_SIZE
        plock_data = bytes(self._data[plock_offset:plock_offset + PLOCK_SIZE])

        step = AudioStep.read(step_num, active, trigless, condition_data, plock_data)
        # Connect sync callback so step changes immediately update the buffer
        step._sync_callback = self._on_step_changed
        return step

    def _on_step_changed(self, step: AudioStep):
        """Called when a step's active/trigless state changes. Syncs to buffer."""
        self._sync_step_to_buffer(step.step_num, step)

    def set_step(self, step_num: int, step: AudioStep):
        """
        Set a step at the given position.

        Args:
            step_num: Step number (1-64)
            step: AudioStep to set
        """
        if step_num < 1 or step_num > 64:
            raise ValueError(f"Step number must be 1-64, got {step_num}")

        # Update step's internal step_num to match position
        step._step_num = step_num
        # Connect sync callback
        step._sync_callback = self._on_step_changed
        self._steps[step_num] = step
        # Sync immediately to buffer
        self._sync_step_to_buffer(step_num, step)

    # === Trig mask properties ===

    @property
    def active_steps(self) -> List[int]:
        """Get/set active trigger steps (1-indexed list)."""
        return _trig_mask_to_steps(self._data, AudioTrackOffset.TRIG_TRIGGER)

    @active_steps.setter
    def active_steps(self, value: List[int]):
        _steps_to_trig_mask(self._data, AudioTrackOffset.TRIG_TRIGGER, value)
        # Also update any loaded step objects
        for step_num in range(1, 65):
            if step_num in self._steps:
                self._steps[step_num].active = step_num in value

    @property
    def trigless_steps(self) -> List[int]:
        """Get/set trigless (envelope) steps (1-indexed list)."""
        return _trig_mask_to_steps(self._data, AudioTrackOffset.TRIG_TRIGLESS)

    @trigless_steps.setter
    def trigless_steps(self, value: List[int]):
        _steps_to_trig_mask(self._data, AudioTrackOffset.TRIG_TRIGLESS, value)
        # Also update any loaded step objects
        for step_num in range(1, 65):
            if step_num in self._steps:
                self._steps[step_num].trigless = step_num in value

    # === Serialization ===

    def to_dict(self, include_steps: bool = False) -> dict:
        """
        Convert pattern track to dictionary.

        Args:
            include_steps: If True, include all steps with data.

        Returns:
            Dict with track number, active_steps, trigless_steps, and optionally steps.
        """
        result = {
            "track": self._track_num,
            "length": self.length,
            "scale": self.scale,
            "active_steps": self.active_steps,
            "trigless_steps": self.trigless_steps,
        }

        if include_steps:
            steps = []
            for step_num in range(1, 65):
                step = self.step(step_num)
                step_dict = step.to_dict()
                # Only include if step has something interesting
                has_data = (
                    step_dict.get("active") or
                    step_dict.get("trigless") or
                    step_dict.get("condition") or
                    len(step_dict) > 3  # More than step/active/trigless
                )
                if has_data:
                    steps.append(step_dict)
            if steps:
                result["steps"] = steps

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AudioPatternTrack":
        """Create an AudioPatternTrack from a dictionary."""
        track = cls(
            track_num=data.get("track", 1),
            active_steps=data.get("active_steps"),
            trigless_steps=data.get("trigless_steps"),
            length=data.get("length", 16),
            scale=data.get("scale", 2),
        )

        # Apply step data if present
        if "steps" in data:
            for step_data in data["steps"]:
                step = AudioStep.from_dict(step_data)
                track.set_step(step.step_num, step)

        return track

    def __eq__(self, other) -> bool:
        """Check equality based on data buffer."""
        if not isinstance(other, AudioPatternTrack):
            return NotImplemented
        return self._track_num == other._track_num and self._data == other._data

    def __repr__(self) -> str:
        active_count = len(self.active_steps)
        return f"AudioPatternTrack(track={self._track_num}, active_steps={active_count})"
