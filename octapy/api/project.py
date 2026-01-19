"""
Project class - main entry point for the high-level API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .._io import (
    BankFile,
    MarkersFile,
    ProjectFile,
    SampleSlot,
    zip_project,
    unzip_project,
)
from .bank import Bank
from .settings import Settings
from .slot_manager import SlotManager


class Project:
    """
    High-level representation of an Octatrack project.

    Combines all .work files (banks, project.work, markers.work) into a single
    abstraction. Handles loading/saving from directories or zip files.

    Usage:
        from octapy import Project, MachineType, TrigCondition

        # Create from template
        project = Project.from_template("MY PROJECT")

        # Sound configuration via Part -> PartTrack
        bank = project.bank(1)
        part = bank.part(1)
        track = part.track(1)
        track.machine_type = MachineType.FLEX
        track.flex_slot = 0

        # Sequence programming via Pattern -> PatternTrack -> Step
        pattern = bank.pattern(1)
        pattern.part = 1
        pattern.track(1).active_steps = [1, 5, 9, 13]
        pattern.track(1).step(5).condition = TrigCondition.FILL

        # Add a sample
        project.add_sample(slot=1, path="../AUDIO/kick.wav")

        # Save as zip
        project.to_zip("/path/to/output.zip")
    """

    def __init__(self, name: str, _internal: bool = False):
        """
        Internal constructor. Use from_template(), from_directory(), or from_zip().
        """
        if not _internal:
            raise TypeError(
                "Project cannot be instantiated directly. "
                "Use Project.from_template(), Project.from_directory(), or Project.from_zip()."
            )
        self.name = name.upper()
        self._project_file = ProjectFile()
        self._markers = None
        self._bank_files: Dict[int, BankFile] = {}
        self._banks: Dict[int, Bank] = {}
        self._arr_files: Dict[int, bytes] = {}  # arr file raw data

        # Sample pool: filename -> local Path (for bundling samples with project)
        self._sample_pool: Dict[str, Path] = {}

        # Slot management
        self._slot_manager = SlotManager()

        # Temp directory reference (kept alive when loading from zip)
        self._temp_dir = None

        # Sample normalization (None = no normalization)
        self._sample_duration = None

    @classmethod
    def from_template(cls, name: str) -> "Project":
        """
        Create a new project from the embedded template.

        Loads ALL template files (16 banks, 8 arr files, markers, project).

        Args:
            name: Project name (will be uppercased)

        Returns:
            New Project instance with default template data
        """
        from .._io.project import read_template_file

        project = cls(name, _internal=True)
        project._project_file = ProjectFile.new()
        project._markers = MarkersFile.new()

        # Load all 16 banks
        for i in range(1, 17):
            project._bank_files[i] = BankFile.new(i)

        # Load all 8 arr files (stored as raw bytes)
        for i in range(1, 9):
            project._arr_files[i] = read_template_file(f"arr{i:02d}.work")

        # Apply sensible sampler defaults
        project._apply_sampler_defaults()

        return project

    @classmethod
    def from_directory(cls, path: Path) -> "Project":
        """
        Load a project from a directory.

        Args:
            path: Path to project directory containing .work files

        Returns:
            Project instance
        """
        path = Path(path)
        name = path.name

        project = cls(name, _internal=True)

        # Load project.work
        project_work = path / "project.work"
        if project_work.exists():
            project._project_file = ProjectFile.from_file(project_work)

        # Load markers.work
        markers_work = path / "markers.work"
        if markers_work.exists():
            project._markers = MarkersFile.from_file(markers_work)

        # Load bank files
        for i in range(1, 17):
            bank_path = path / f"bank{i:02d}.work"
            if bank_path.exists():
                project._bank_files[i] = BankFile.from_file(bank_path)

        # Load arr files (as raw bytes)
        for i in range(1, 9):
            arr_path = path / f"arr{i:02d}.work"
            if arr_path.exists():
                project._arr_files[i] = arr_path.read_bytes()

        # Initialize slot tracking from existing samples
        project._init_slots_from_project_file()

        # Load bundled samples from samples/ subdirectory
        samples_dir = path / "samples"
        if samples_dir.exists():
            for sample_file in samples_dir.glob("*.wav"):
                project._sample_pool[sample_file.name] = sample_file

        return project

    def _init_slots_from_project_file(self) -> None:
        """Initialize slot tracking from existing sample slots in project file."""
        self._slot_manager.load_from_slots(self._project_file.sample_slots)

    @classmethod
    def from_zip(cls, zip_path: Path) -> "Project":
        """
        Load a project from a zip file.

        Zip structure:
            project/   - .work files
            samples/   - .wav files

        Args:
            zip_path: Path to project zip file

        Returns:
            Project instance
        """
        import tempfile

        # Create temp dir that persists for lifetime of Project object
        # (needed to keep bundled sample paths valid)
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_path = Path(tmp_dir.name)
        unzip_project(zip_path, tmp_path)

        # Load .work files from project/ subdirectory
        project_subdir = tmp_path / "project"
        if project_subdir.exists():
            project = cls.from_directory(project_subdir)
        else:
            # Fallback for old flat structure
            project = cls.from_directory(tmp_path)

        project.name = Path(zip_path).stem.upper()
        project._temp_dir = tmp_dir  # Keep alive until Project is garbage collected

        # Load samples from samples/ subdirectory
        samples_dir = tmp_path / "samples"
        if samples_dir.exists():
            for sample_file in samples_dir.glob("*.wav"):
                project._sample_pool[sample_file.name] = sample_file

        return project

    def to_directory(self, path: Path) -> None:
        """
        Save the project to a directory.

        Writes all files (project, markers, banks, arr files).

        Args:
            path: Destination directory (will be created if needed)
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save project.work
        self._project_file.to_file(path / "project.work")

        # Save markers.work
        if self._markers:
            self._markers.to_file(path / "markers.work")

        # Save all bank files
        for bank_num, bank_file in self._bank_files.items():
            bank_file.to_file(path / f"bank{bank_num:02d}.work")

        # Save all arr files
        for arr_num, arr_data in self._arr_files.items():
            (path / f"arr{arr_num:02d}.work").write_bytes(arr_data)

        # Save samples from pool (with optional normalization)
        if self._sample_pool:
            samples_dir = path / "samples"
            samples_dir.mkdir(exist_ok=True)

            if self._sample_duration is not None:
                # Normalize samples to target duration
                target_ms = _calculate_duration_ms(self.settings.tempo, self._sample_duration)
                for filename, local_path in self._sample_pool.items():
                    _normalize_sample(local_path, samples_dir / filename, target_ms)
            else:
                # Copy samples without normalization
                import shutil
                for filename, local_path in self._sample_pool.items():
                    shutil.copy2(local_path, samples_dir / filename)

    def to_zip(self, zip_path: Path) -> None:
        """
        Save the project to a zip file.

        Args:
            zip_path: Path for output zip file
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / self.name
            self.to_directory(tmp_path)
            zip_project(tmp_path, zip_path)

    # === Bank access ===

    def bank(self, bank_num: int = 1) -> Bank:
        """
        Get a bank (lazy loaded from template if not present).

        Args:
            bank_num: Bank number (1-16)

        Returns:
            Bank instance for configuring patterns and parts
        """
        if bank_num not in self._bank_files:
            self._bank_files[bank_num] = BankFile.new(bank_num)
        if bank_num not in self._banks:
            self._banks[bank_num] = Bank(self, bank_num, self._bank_files[bank_num])
        return self._banks[bank_num]

    @property
    def markers(self) -> MarkersFile:
        """Get the markers file (lazy loaded from template if not present)."""
        if self._markers is None:
            self._markers = MarkersFile.new()
        return self._markers

    @property
    def settings(self) -> Settings:
        """Get project settings (tempo, MIDI, recorder, etc.)."""
        if not hasattr(self, '_settings') or self._settings is None:
            self._settings = Settings(self._project_file.settings)
        return self._settings

    @property
    def sample_duration(self):
        """
        Get/set sample duration for normalization.

        When set, samples are normalized (trimmed/padded) to this duration
        based on BPM when saving the project.

        Values: NoteLength.SIXTEENTH (1 step), EIGHTH (2 steps),
                QUARTER (4 steps), HALF (8 steps), WHOLE (16 steps),
                or None (no normalization)
        """
        return self._sample_duration

    @sample_duration.setter
    def sample_duration(self, value):
        self._sample_duration = value

    # === Sample management ===

    def _update_flex_count(self) -> None:
        """Update flex_count in all loaded banks."""
        for bank_file in self._bank_files.values():
            bank_file.flex_count = self._slot_manager.flex_count

    def add_sample(
        self,
        local_path: Path,
        slot_type: str = "FLEX",
        slot: Optional[int] = None,
        gain: int = 48,
    ) -> int:
        """
        Add a sample to the project from a local file.

        The sample is added to the sample pool and will be bundled with the
        project when saved. The OT path is auto-generated as:
        ../AUDIO/projects/{PROJECT_NAME}/{filename}.wav

        If the same filename has already been added, returns the existing slot.
        If no slot is specified, automatically assigns the next available slot.

        Args:
            local_path: Local path to WAV file
            slot_type: "FLEX" or "STATIC"
            slot: Slot number (1-128). If None, auto-assigns next available.
            gain: Gain value 0-127 (48 = 0dB)

        Returns:
            The assigned slot number

        Raises:
            SlotLimitExceeded: If all 128 slots for this type are in use
            InvalidSlotNumber: If explicit slot number is out of range
            FileNotFoundError: If local_path doesn't exist
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Sample file not found: {local_path}")

        filename = local_path.name
        ot_path = f"../AUDIO/projects/{self.name}/{filename}"
        is_flex = slot_type.upper() == "FLEX"

        # Check if already assigned (returns existing slot)
        existing = self._slot_manager.get(ot_path, slot_type)
        if existing is not None:
            return existing

        # Assign slot (auto or explicit)
        slot = self._slot_manager.assign(ot_path, slot_type, slot)

        # Add to sample pool
        self._sample_pool[filename] = local_path

        # Add to project.work
        self._project_file.add_sample_slot(
            slot_number=slot,
            path=ot_path,
            slot_type=slot_type,
            gain=gain,
        )

        # Update markers.work with sample length
        frame_count = _get_wav_frame_count(local_path)
        if frame_count > 0:
            self.markers.set_sample_length(slot, frame_count, is_static=not is_flex)

        # Auto-update flex_count in banks
        if is_flex:
            self._update_flex_count()

        return slot

    def get_slot(self, filename: str, slot_type: str = "FLEX") -> Optional[int]:
        """
        Get the slot number assigned to a sample by filename.

        Args:
            filename: The sample filename (e.g., "kick.wav")
            slot_type: "FLEX" or "STATIC"

        Returns:
            Slot number if found, None otherwise
        """
        ot_path = f"../AUDIO/projects/{self.name}/{filename}"
        return self._slot_manager.get(ot_path, slot_type)

    @property
    def flex_slot_count(self) -> int:
        """Number of flex sample slots in use."""
        return self._slot_manager.flex_count

    @property
    def static_slot_count(self) -> int:
        """Number of static sample slots in use."""
        return self._slot_manager.static_count

    @property
    def sample_paths(self) -> list:
        """List of all OT sample paths (flex and static) in the project."""
        return self._slot_manager.flex_paths + self._slot_manager.static_paths

    @property
    def sample_pool(self) -> Dict[str, Path]:
        """Sample pool: filename -> local path mapping."""
        return self._sample_pool.copy()

    def add_recorder_slots(self) -> None:
        """Add the 8 recorder buffer slots (129-136)."""
        self._project_file.add_recorder_slots()

    def _apply_sampler_defaults(self) -> None:
        """
        Apply sensible sampler defaults to all banks/parts/tracks.

        For Flex machines only, sets:
        - loop_mode = OFF (no looping by default)
        - length_mode = TIME so LEN encoder works for truncating samples
        - length = 127 (max) so samples play fully by default
        """
        from .enums import LoopMode, LengthMode

        # Apply to all 16 banks, 4 parts, 8 tracks (Flex only)
        for bank_num in range(1, 17):
            bank = self.bank(bank_num)
            for part_num in range(1, 5):
                part = bank.part(part_num)
                for track_num in range(1, 9):
                    flex = part.flex_track(track_num)
                    flex.loop_mode = LoopMode.OFF
                    flex.length_mode = LengthMode.TIME
                    flex.length = 127


def _get_wav_frame_count(wav_path: Path) -> int:
    """Get the number of audio frames in a WAV file."""
    import wave

    try:
        with wave.open(str(wav_path), 'rb') as w:
            return w.getnframes()
    except Exception:
        return 0


def _calculate_duration_ms(bpm: float, note_length) -> int:
    """
    Calculate target sample duration in milliseconds.

    Args:
        bpm: Project tempo in BPM
        note_length: NoteLength enum value (MIDI ticks at 24 PPQN)

    Returns:
        Duration in milliseconds
    """
    # NoteLength values are ticks at 24 PPQN (24 ticks per quarter note)
    # duration = (60 / bpm) * (ticks / 24) seconds
    seconds = (60.0 / bpm) * (int(note_length) / 24.0)
    return int(seconds * 1000)


def _normalize_sample(source_path: Path, dest_path: Path, target_ms: int) -> None:
    """
    Normalize a sample to a target duration.

    Trims (with 3ms fade out) or pads with silence as needed.

    Args:
        source_path: Path to source WAV file
        dest_path: Path to write normalized WAV file
        target_ms: Target duration in milliseconds
    """
    from pydub import AudioSegment

    audio = AudioSegment.from_wav(str(source_path))
    current_ms = len(audio)

    if current_ms > target_ms:
        # Trim with fade out to avoid clicks
        audio = audio[:target_ms].fade_out(3)
    elif current_ms < target_ms:
        # Pad with silence
        silence = AudioSegment.silent(duration=target_ms - current_ms)
        audio = audio + silence

    audio.export(str(dest_path), format="wav")
