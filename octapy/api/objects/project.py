"""
Project - standalone Project container with Banks, settings, and markers.

This is a standalone object that owns its data and can be created
with constructor arguments or read from a project directory/zip.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..._io import (
    ProjectFile,
    MarkersFile,
    SampleSlot,
    zip_project,
    unzip_project,
)
from ..settings import Settings, RenderSettings
from ..slot_manager import SlotManager
from .bank import Bank


class Project:
    """
    Project containing 16 Banks, settings, and markers.

    This is a standalone object that owns all its data:
    - 16 Bank objects (each with 4 Parts and 16 Patterns)
    - ProjectFile for settings (tempo, MIDI config, etc.)
    - MarkersFile for sample lengths
    - Sample slot assignments

    Usage:
        # Create with constructor arguments
        project = Project(name="MY PROJECT", tempo=120.0)
        project.bank(1).part(1).audio_track(1).machine_type = MachineType.FLEX
        project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]

        # Read from directory
        project = Project.from_directory("/path/to/project")

        # Read from zip
        project = Project.from_zip("/path/to/project.zip")

        # Write to directory
        project.to_directory("/path/to/output")

        # Write to zip
        project.to_zip("/path/to/output.zip")

        # Create from template with octapy defaults
        project = Project.from_template("MY PROJECT")
    """

    def __init__(
        self,
        name: str = "UNTITLED",
        tempo: float = 120.0,
        banks: Optional[List[Bank]] = None,
    ):
        """
        Create a Project with optional configurations.

        Args:
            name: Project name (will be uppercased)
            tempo: Project tempo in BPM (default 120.0)
            banks: Optional list of 16 Bank objects
        """
        self._name = name.upper()
        self._project_file = ProjectFile()
        self._project_file.tempo = tempo
        self._markers = MarkersFile.new() if MarkersFile else None
        self._arr_files: Dict[int, bytes] = {}

        # Initialize banks
        self._banks: Dict[int, Bank] = {}
        for i in range(1, 17):
            self._banks[i] = Bank(bank_num=i)

        # Apply provided banks
        if banks:
            for bank in banks:
                self._banks[bank.bank_num] = bank

        # Sample pool: filename -> local Path (for bundling samples with project)
        self._sample_pool: Dict[str, Path] = {}

        # Slot manager for tracking sample slot assignments
        self._slot_manager = SlotManager()

        # Temp directory reference (kept alive when loading from zip)
        self._temp_dir = None

        # Octapy rendering settings (not saved to OT files)
        self._render_settings = RenderSettings()
        self._settings = None  # Lazily initialized

    @classmethod
    def from_template(cls, name: str) -> "Project":
        """
        Create a new project from the embedded template.

        Applies octapy default overrides for better workflows:
        - SRC page: loop_mode=OFF, length_mode=TIME, length=127
        - Recorder: RLEN=16, QREC=PLEN, all sources OFF

        Args:
            name: Project name (will be uppercased)

        Returns:
            Project instance with octapy defaults
        """
        from ..._io.project import read_template_file

        instance = cls.__new__(cls)
        instance._name = name.upper()
        instance._project_file = ProjectFile.new()
        instance._markers = MarkersFile.new()
        instance._arr_files = {}
        instance._banks = {}
        instance._sample_pool = {}
        instance._slot_manager = SlotManager()
        instance._temp_dir = None
        instance._render_settings = RenderSettings()
        instance._settings = None

        # Load all 16 banks from template with octapy defaults
        for i in range(1, 17):
            instance._banks[i] = Bank.from_template(bank_num=i)

        # Load all 8 arr files (stored as raw bytes)
        for i in range(1, 9):
            instance._arr_files[i] = read_template_file(f"arr{i:02d}.work")

        return instance

    @classmethod
    def from_directory(cls, path: Path | str) -> "Project":
        """
        Load a project from a directory.

        Args:
            path: Path to project directory containing .work files

        Returns:
            Project instance
        """
        path = Path(path)
        name = path.name

        instance = cls.__new__(cls)
        instance._name = name.upper()
        instance._banks = {}
        instance._arr_files = {}
        instance._sample_pool = {}
        instance._slot_manager = SlotManager()
        instance._temp_dir = None
        instance._render_settings = RenderSettings()
        instance._settings = None

        # Load project.work
        project_work = path / "project.work"
        if project_work.exists():
            instance._project_file = ProjectFile.from_file(project_work)
            # Initialize slot manager from existing slots
            instance._slot_manager.load_from_slots(instance._project_file.sample_slots)
        else:
            instance._project_file = ProjectFile()

        # Load markers.work
        markers_work = path / "markers.work"
        if markers_work.exists():
            instance._markers = MarkersFile.from_file(markers_work)
        else:
            instance._markers = MarkersFile.new()

        # Load bank files
        for i in range(1, 17):
            bank_path = path / f"bank{i:02d}.work"
            if bank_path.exists():
                instance._banks[i] = Bank.from_file(bank_path)
            else:
                instance._banks[i] = Bank(bank_num=i)

        # Load arr files (as raw bytes)
        for i in range(1, 9):
            arr_path = path / f"arr{i:02d}.work"
            if arr_path.exists():
                instance._arr_files[i] = arr_path.read_bytes()

        # Load bundled samples from samples/ subdirectory
        samples_dir = path / "samples"
        if samples_dir.exists():
            for sample_file in samples_dir.glob("*.wav"):
                instance._sample_pool[sample_file.name] = sample_file

        return instance

    @classmethod
    def from_zip(cls, zip_path: Path | str) -> "Project":
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

        zip_path = Path(zip_path)

        # Create temp dir that persists for lifetime of Project object
        # (needed to keep bundled sample paths valid)
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_path = Path(tmp_dir.name)
        unzip_project(zip_path, tmp_path)

        # Load .work files from project/ subdirectory
        project_subdir = tmp_path / "project"
        if project_subdir.exists():
            instance = cls.from_directory(project_subdir)
        else:
            # Fallback for old flat structure
            instance = cls.from_directory(tmp_path)

        instance._name = zip_path.stem.upper()
        instance._temp_dir = tmp_dir  # Keep alive until Project is garbage collected

        # Load samples from samples/ subdirectory
        samples_dir = tmp_path / "samples"
        if samples_dir.exists():
            for sample_file in samples_dir.glob("*.wav"):
                instance._sample_pool[sample_file.name] = sample_file

        return instance

    def to_directory(self, path: Path | str) -> None:
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
        for bank_num in range(1, 17):
            self._banks[bank_num].to_file(path / f"bank{bank_num:02d}.work")

        # Save all arr files
        for arr_num, arr_data in self._arr_files.items():
            (path / f"arr{arr_num:02d}.work").write_bytes(arr_data)

        # Save samples from pool
        if self._sample_pool:
            samples_dir = path / "samples"
            samples_dir.mkdir(exist_ok=True)
            import shutil
            for filename, local_path in self._sample_pool.items():
                shutil.copy2(local_path, samples_dir / filename)

    def to_zip(self, zip_path: Path | str) -> None:
        """
        Save the project to a zip file.

        Args:
            zip_path: Path for output zip file
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / self._name
            self.to_directory(tmp_path)
            zip_project(tmp_path, Path(zip_path))

    def clone(self) -> "Project":
        """Create a copy of this Project with all banks cloned."""
        from copy import deepcopy

        instance = Project.__new__(Project)
        instance._name = self._name
        instance._project_file = ProjectFile()
        instance._project_file.settings = deepcopy(self._project_file.settings)
        instance._project_file.state = deepcopy(self._project_file.state)
        instance._project_file.sample_slots = deepcopy(self._project_file.sample_slots)

        if self._markers:
            # Clone markers by reading the written data
            instance._markers = MarkersFile.new()
            instance._markers._data = bytearray(self._markers._data)
        else:
            instance._markers = None

        instance._arr_files = dict(self._arr_files)

        # Clone banks
        instance._banks = {}
        for i, bank in self._banks.items():
            instance._banks[i] = bank.clone()

        instance._sample_pool = dict(self._sample_pool)
        instance._temp_dir = None
        instance._render_settings = RenderSettings()
        instance._settings = None

        return instance

    # === Basic properties ===

    @property
    def name(self) -> str:
        """Get/set the project name."""
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value.upper()

    @property
    def tempo(self) -> float:
        """Get/set the project tempo in BPM."""
        return self._project_file.tempo

    @tempo.setter
    def tempo(self, value: float):
        self._project_file.tempo = value

    @property
    def master_track(self) -> bool:
        """Get/set whether master track is enabled (track 8 sums tracks 1-7)."""
        return self._project_file.settings.master_track == 1

    @master_track.setter
    def master_track(self, value: bool):
        self._project_file.settings.master_track = 1 if value else 0

    @property
    def settings(self) -> Settings:
        """Get project settings (tempo, MIDI, recorder, etc.)."""
        if self._settings is None:
            self._settings = Settings(self._project_file.settings)
        return self._settings

    @property
    def render_settings(self) -> RenderSettings:
        """
        Get octapy rendering settings.

        These settings control octapy's behavior during project processing
        and saving. They are NOT saved to Octatrack files.

        Available settings:
            auto_master_trig: Auto-add track 8 trig when master track enabled
            auto_thru_trig: Auto-add trig to Thru machine tracks
            propagate_scenes: Copy scenes from Part 1 to Parts 2-4
            propagate_src: Copy SRC page from Part 1 to Parts 2-4
            sample_duration: Target duration for sample normalization
        """
        return self._render_settings

    @property
    def sample_duration(self):
        """
        Get/set sample duration for normalization.

        Shortcut for render_settings.sample_duration.

        When set, samples are normalized (trimmed/padded) to this duration
        based on BPM when saving the project.

        Values: NoteLength.SIXTEENTH (1 step), EIGHTH (2 steps),
                QUARTER (4 steps), HALF (8 steps), WHOLE (16 steps),
                or None (no normalization, default)
        """
        return self._render_settings.sample_duration

    @sample_duration.setter
    def sample_duration(self, value):
        self._render_settings.sample_duration = value

    # === Bank access ===

    def bank(self, bank_num: int) -> Bank:
        """
        Get a bank (1-16).

        Args:
            bank_num: Bank number (1-16)

        Returns:
            Bank instance
        """
        if bank_num < 1 or bank_num > 16:
            raise ValueError(f"Bank number must be 1-16, got {bank_num}")
        return self._banks[bank_num]

    def set_bank(self, bank_num: int, bank: Bank):
        """
        Set a bank at the given position.

        Args:
            bank_num: Bank number (1-16)
            bank: Bank to set
        """
        if bank_num < 1 or bank_num > 16:
            raise ValueError(f"Bank number must be 1-16, got {bank_num}")
        bank._bank_num = bank_num
        self._banks[bank_num] = bank

    # === Markers access ===

    @property
    def markers(self) -> MarkersFile:
        """Get the markers file."""
        if self._markers is None:
            self._markers = MarkersFile.new()
        return self._markers

    # === Sample management ===

    def add_sample(
        self,
        local_path: Path | str,
        slot_type: str = "FLEX",
        slot: Optional[int] = None,
        gain: int = 48,
    ) -> int:
        """
        Add a sample to the project from a local file.

        The sample is added to the sample pool and will be bundled with the
        project when saved. The OT path is auto-generated as:
        ../AUDIO/projects/{PROJECT_NAME}/{filename}.wav

        Args:
            local_path: Local path to WAV file
            slot_type: "FLEX" or "STATIC"
            slot: Slot number (1-128). If None, auto-assigns next available.
            gain: Gain value 0-127 (48 = 0dB)

        Returns:
            The assigned slot number

        Raises:
            FileNotFoundError: If local_path doesn't exist
            InvalidSlotNumber: If slot is out of range (1-128) or already in use
            SlotLimitExceeded: If auto-assigning and all slots are used
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Sample file not found: {local_path}")

        filename = local_path.name
        ot_path = f"../AUDIO/projects/{self._name}/{filename}"
        is_flex = slot_type.upper() == "FLEX"

        # Check if this path already has a slot assigned
        existing_slot = self._slot_manager.get(ot_path, slot_type)
        if existing_slot is not None:
            return existing_slot

        # Use slot manager for validation and assignment
        # (handles range validation, duplicate check, auto-assign)
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
        if frame_count > 0 and self._markers:
            self._markers.set_sample_length(slot, frame_count, is_static=not is_flex)

        # Auto-update flex_count in banks
        if is_flex:
            flex_count = sum(1 for s in self._project_file.sample_slots
                            if s.slot_type == "FLEX" and s.slot_number <= 128)
            for bank in self._banks.values():
                bank.flex_count = flex_count

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
        ot_path = f"../AUDIO/projects/{self._name}/{filename}"
        for slot in self._project_file.sample_slots:
            if slot.path == ot_path and slot.slot_type == slot_type.upper():
                return slot.slot_number
        return None

    @property
    def flex_slot_count(self) -> int:
        """Number of flex sample slots in use."""
        return sum(1 for s in self._project_file.sample_slots
                   if s.slot_type == "FLEX" and s.slot_number <= 128)

    @property
    def static_slot_count(self) -> int:
        """Number of static sample slots in use."""
        return sum(1 for s in self._project_file.sample_slots
                   if s.slot_type == "STATIC" and s.slot_number <= 128)

    @property
    def sample_pool(self) -> Dict[str, Path]:
        """Sample pool: filename -> local path mapping."""
        return self._sample_pool.copy()

    def add_recorder_slots(self) -> None:
        """Add the 8 recorder buffer slots (129-136)."""
        self._project_file.add_recorder_slots()

    # === Serialization ===

    def to_dict(self, include_steps: bool = False, include_scenes: bool = False) -> dict:
        """
        Convert project to dictionary.

        Args:
            include_steps: Include step data in patterns (default False)
            include_scenes: Include scene locks in parts (default False)

        Returns:
            Dict with project name, tempo, banks, and sample info.
        """
        return {
            "name": self._name,
            "tempo": self.tempo,
            "flex_slot_count": self.flex_slot_count,
            "static_slot_count": self.static_slot_count,
            "banks": [self._banks[n].to_dict(include_steps=include_steps, include_scenes=include_scenes)
                      for n in range(1, 17)],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Create a Project from a dictionary."""
        project = cls(
            name=data.get("name", "UNTITLED"),
            tempo=data.get("tempo", 120.0),
        )

        if "banks" in data:
            for bank_data in data["banks"]:
                bank = Bank.from_dict(bank_data)
                project._banks[bank.bank_num] = bank

        return project

    def __eq__(self, other) -> bool:
        """Check equality based on all contained objects."""
        if not isinstance(other, Project):
            return NotImplemented
        if self._name != other._name:
            return False
        if self.tempo != other.tempo:
            return False
        if self._banks != other._banks:
            return False
        return True

    def __repr__(self) -> str:
        return f"Project(name={self._name!r}, tempo={self.tempo}, banks=16)"


def _get_wav_frame_count(wav_path: Path) -> int:
    """Get the number of audio frames in a WAV file."""
    import wave

    try:
        with wave.open(str(wav_path), 'rb') as w:
            return w.getnframes()
    except Exception:
        return 0
