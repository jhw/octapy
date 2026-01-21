"""
Part - standalone Part container with tracks and scenes.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Bank binary data.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..._io import (
    PartOffset,
    SceneOffset,
    MidiPartOffset,
    SCENE_SIZE,
    SCENE_COUNT,
    MIDI_TRACK_VALUES_SIZE,
    MIDI_TRACK_SETUP_SIZE,
)
from .audio.part_track import AudioPartTrack, AUDIO_PART_TRACK_SIZE
from .midi.part_track import MidiPartTrack, MIDI_PART_TRACK_SIZE
from .scene import Scene


# Part block size (matches OT format)
PART_BLOCK_SIZE = 6331


class Part:
    """
    Part containing track configurations and scenes.

    This is a standalone object that contains:
    - 8 AudioPartTrack objects (machine configurations)
    - 8 MidiPartTrack objects (MIDI configurations)
    - 16 Scene objects (crossfader locks)
    - Part settings (active scenes)

    Usage:
        # Create with constructor arguments
        part = Part(part_num=1)
        part.audio_track(1).machine_type = MachineType.FLEX
        part.audio_track(1).fx1_type = FX1Type.FILTER

        # Read from Bank binary (called by Bank)
        part = Part.read_from_bank(part_num, bank_data, part_offset)

        # Write to binary
        part.write_to_bank(bank_data, part_offset)
    """

    def __init__(
        self,
        part_num: int = 1,
        active_scene_a: int = 0,
        active_scene_b: int = 0,
        audio_tracks: Optional[List[AudioPartTrack]] = None,
        midi_tracks: Optional[List[MidiPartTrack]] = None,
        scenes: Optional[List[Scene]] = None,
    ):
        """
        Create a Part with optional configurations.

        Args:
            part_num: Part number (1-4)
            active_scene_a: Active scene A (0-15)
            active_scene_b: Active scene B (0-15)
            audio_tracks: Optional list of 8 AudioPartTrack objects
            midi_tracks: Optional list of 8 MidiPartTrack objects
            scenes: Optional list of 16 Scene objects
        """
        self._part_num = part_num
        self._active_scene_a = active_scene_a
        self._active_scene_b = active_scene_b

        # Initialize track collections
        self._audio_tracks: Dict[int, AudioPartTrack] = {}
        self._midi_tracks: Dict[int, MidiPartTrack] = {}
        self._scenes: Dict[int, Scene] = {}

        # Create default audio tracks
        for i in range(1, 9):
            self._audio_tracks[i] = AudioPartTrack(track_num=i)

        # Create default MIDI tracks
        for i in range(1, 9):
            self._midi_tracks[i] = MidiPartTrack(track_num=i)

        # Create default scenes
        for i in range(1, 17):
            self._scenes[i] = Scene(scene_num=i)

        # Apply provided tracks/scenes
        if audio_tracks:
            for track in audio_tracks:
                self._audio_tracks[track.track_num] = track

        if midi_tracks:
            for track in midi_tracks:
                self._midi_tracks[track.track_num] = track

        if scenes:
            for scene in scenes:
                self._scenes[scene.scene_num] = scene

    @classmethod
    def read_from_bank(cls, part_num: int, bank_data: bytes, part_offset: int = 0) -> "Part":
        """
        Read a Part from Bank binary data.

        Reads the scattered Part data from the bank file and creates
        standalone objects for tracks and scenes.

        Args:
            part_num: Part number (1-4)
            bank_data: Bank binary data
            part_offset: Offset to Part data in bank_data buffer

        Returns:
            Part instance
        """
        instance = cls.__new__(cls)
        instance._part_num = part_num

        # Read settings
        instance._active_scene_a = bank_data[part_offset + PartOffset.ACTIVE_SCENE_A]
        instance._active_scene_b = bank_data[part_offset + PartOffset.ACTIVE_SCENE_B]

        # Read audio tracks
        instance._audio_tracks = {}
        for i in range(1, 9):
            track = AudioPartTrack.read_from_part(i, bank_data, part_offset)
            instance._audio_tracks[i] = track

        # Read MIDI tracks
        instance._midi_tracks = {}
        for i in range(1, 9):
            track = MidiPartTrack.read_from_part(i, bank_data, part_offset)
            instance._midi_tracks[i] = track

        # Read scenes
        instance._scenes = {}
        scenes_base = part_offset + SceneOffset.SCENES
        for i in range(1, 17):
            scene_offset = scenes_base + (i - 1) * SCENE_SIZE
            scene_data = bank_data[scene_offset:scene_offset + SCENE_SIZE]
            instance._scenes[i] = Scene.read(i, scene_data)

        return instance

    def write_to_bank(self, bank_data: bytearray, part_offset: int = 0):
        """
        Write this Part to Bank binary data.

        Writes to the scattered locations in the bank file.

        Args:
            bank_data: Bank binary data (modified in place)
            part_offset: Offset to Part data in bank_data buffer
        """
        # Write settings
        bank_data[part_offset + PartOffset.ACTIVE_SCENE_A] = self._active_scene_a & 0x0F
        bank_data[part_offset + PartOffset.ACTIVE_SCENE_B] = self._active_scene_b & 0x0F

        # Write audio tracks
        for i in range(1, 9):
            self._audio_tracks[i].write_to_part(bank_data, part_offset)

        # Write MIDI tracks
        for i in range(1, 9):
            self._midi_tracks[i].write_to_part(bank_data, part_offset)

        # Write scenes
        scenes_base = part_offset + SceneOffset.SCENES
        for i in range(1, 17):
            scene_offset = scenes_base + (i - 1) * SCENE_SIZE
            scene_data = self._scenes[i].write()
            bank_data[scene_offset:scene_offset + SCENE_SIZE] = scene_data

    def clone(self) -> "Part":
        """Create a copy of this Part with all tracks and scenes cloned."""
        instance = Part.__new__(Part)
        instance._part_num = self._part_num
        instance._active_scene_a = self._active_scene_a
        instance._active_scene_b = self._active_scene_b

        # Clone audio tracks
        instance._audio_tracks = {}
        for i, track in self._audio_tracks.items():
            instance._audio_tracks[i] = track.clone()

        # Clone MIDI tracks
        instance._midi_tracks = {}
        for i, track in self._midi_tracks.items():
            instance._midi_tracks[i] = track.clone()

        # Clone scenes
        instance._scenes = {}
        for i, scene in self._scenes.items():
            instance._scenes[i] = scene.clone()

        return instance

    # === Basic properties ===

    @property
    def part_num(self) -> int:
        """Get the part number (1-4)."""
        return self._part_num

    @property
    def active_scene_a(self) -> int:
        """Get/set active scene A (0-15)."""
        return self._active_scene_a

    @active_scene_a.setter
    def active_scene_a(self, value: int):
        self._active_scene_a = value & 0x0F

    @property
    def active_scene_b(self) -> int:
        """Get/set active scene B (0-15)."""
        return self._active_scene_b

    @active_scene_b.setter
    def active_scene_b(self, value: int):
        self._active_scene_b = value & 0x0F

    # === Track access ===

    def audio_track(self, track_num: int) -> AudioPartTrack:
        """
        Get audio track configuration (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            AudioPartTrack instance
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        return self._audio_tracks[track_num]

    def set_audio_track(self, track_num: int, track: AudioPartTrack):
        """
        Set audio track at the given position.

        Args:
            track_num: Track number (1-8)
            track: AudioPartTrack to set
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        track._track_num = track_num
        self._audio_tracks[track_num] = track

    def midi_track(self, track_num: int) -> MidiPartTrack:
        """
        Get MIDI track configuration (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPartTrack instance
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        return self._midi_tracks[track_num]

    def set_midi_track(self, track_num: int, track: MidiPartTrack):
        """
        Set MIDI track at the given position.

        Args:
            track_num: Track number (1-8)
            track: MidiPartTrack to set
        """
        if track_num < 1 or track_num > 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        track._track_num = track_num
        self._midi_tracks[track_num] = track

    # Alias for backward compatibility
    def track(self, track_num: int) -> AudioPartTrack:
        """Alias for audio_track()."""
        return self.audio_track(track_num)

    # Machine-specific track accessors (convenience methods)
    def flex_track(self, track_num: int) -> AudioPartTrack:
        """Get audio track configured as Flex machine."""
        return self.audio_track(track_num)

    def static_track(self, track_num: int) -> AudioPartTrack:
        """Get audio track configured as Static machine."""
        return self.audio_track(track_num)

    def thru_track(self, track_num: int) -> AudioPartTrack:
        """Get audio track configured as Thru machine."""
        return self.audio_track(track_num)

    def neighbor_track(self, track_num: int) -> AudioPartTrack:
        """Get audio track configured as Neighbor machine."""
        return self.audio_track(track_num)

    # === Scene access ===

    def scene(self, scene_num: int) -> Scene:
        """
        Get a scene (1-16).

        Args:
            scene_num: Scene number (1-16)

        Returns:
            Scene instance
        """
        if scene_num < 1 or scene_num > 16:
            raise ValueError(f"Scene number must be 1-16, got {scene_num}")
        return self._scenes[scene_num]

    def set_scene(self, scene_num: int, scene: Scene):
        """
        Set a scene at the given position.

        Args:
            scene_num: Scene number (1-16)
            scene: Scene to set
        """
        if scene_num < 1 or scene_num > 16:
            raise ValueError(f"Scene number must be 1-16, got {scene_num}")
        scene._scene_num = scene_num
        self._scenes[scene_num] = scene

    # === Serialization ===

    def to_dict(self, include_scenes: bool = False) -> dict:
        """
        Convert part to dictionary.

        Args:
            include_scenes: Include scene locks in output (default False)

        Returns:
            Dict with part number, active scenes, audio tracks, and MIDI tracks.
        """
        result = {
            "part": self._part_num,
            "active_scene_a": self._active_scene_a,
            "active_scene_b": self._active_scene_b,
            "audio_tracks": [self._audio_tracks[n].to_dict() for n in range(1, 9)],
            "midi_tracks": [self._midi_tracks[n].to_dict() for n in range(1, 9)],
        }

        if include_scenes:
            scenes = []
            for n in range(1, 17):
                scene = self._scenes[n]
                if scene.has_locks():
                    scenes.append(scene.to_dict())
            if scenes:
                result["scenes"] = scenes

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Part":
        """Create a Part from a dictionary."""
        part = cls(
            part_num=data.get("part", 1),
            active_scene_a=data.get("active_scene_a", 0),
            active_scene_b=data.get("active_scene_b", 0),
        )

        if "audio_tracks" in data:
            for track_data in data["audio_tracks"]:
                track = AudioPartTrack.from_dict(track_data)
                part._audio_tracks[track.track_num] = track

        if "midi_tracks" in data:
            for track_data in data["midi_tracks"]:
                track = MidiPartTrack.from_dict(track_data)
                part._midi_tracks[track.track_num] = track

        if "scenes" in data:
            for scene_data in data["scenes"]:
                scene = Scene.from_dict(scene_data)
                part._scenes[scene.scene_num] = scene

        return part

    def __eq__(self, other) -> bool:
        """Check equality based on all contained objects."""
        if not isinstance(other, Part):
            return NotImplemented
        if self._part_num != other._part_num:
            return False
        if self._active_scene_a != other._active_scene_a:
            return False
        if self._active_scene_b != other._active_scene_b:
            return False
        if self._audio_tracks != other._audio_tracks:
            return False
        if self._midi_tracks != other._midi_tracks:
            return False
        if self._scenes != other._scenes:
            return False
        return True

    def __repr__(self) -> str:
        return f"Part(part={self._part_num}, scene_a={self._active_scene_a}, scene_b={self._active_scene_b})"
