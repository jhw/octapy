"""
Project class - main entry point for the high-level API.
"""

from pathlib import Path
from typing import Dict, Optional

from .._io import (
    BankFile,
    MarkersFile,
    ProjectFile,
    ProjectSettings,
    SampleSlot,
    zip_project,
    unzip_project,
)
from .bank import Bank
from .base import (
    MAX_FLEX_SAMPLE_SLOTS,
    MAX_STATIC_SAMPLE_SLOTS,
    RECORDER_SLOTS_START,
    SlotLimitExceeded,
    InvalidSlotNumber,
)


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

    def __init__(self, name: str):
        """
        Create an empty project.

        Use from_template(), from_directory(), or from_zip() instead.
        """
        self.name = name.upper()
        self._project_file = ProjectFile()
        self._markers = None  # Lazy loaded
        self._bank_files: Dict[int, BankFile] = {}
        self._banks: Dict[int, Bank] = {}

        # Slot tracking: path -> slot_number (for reuse when same sample added twice)
        self._flex_slots: Dict[str, int] = {}  # path -> slot (1-128)
        self._static_slots: Dict[str, int] = {}  # path -> slot (1-128)

    @classmethod
    def from_template(cls, name: str) -> "Project":
        """
        Create a new project from the embedded template.

        Args:
            name: Project name (will be uppercased)

        Returns:
            New Project instance with default template data
        """
        project = cls(name)
        project._project_file = ProjectFile.new()
        project._markers = MarkersFile.new()
        project._bank_files[1] = BankFile.new(1)

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

        project = cls(name)

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

        # Initialize slot tracking from existing samples
        project._init_slots_from_project_file()

        return project

    def _init_slots_from_project_file(self) -> None:
        """Initialize slot tracking from existing sample slots in project file."""
        for sample_slot in self._project_file.sample_slots:
            slot_num = sample_slot.slot_number
            path = sample_slot.path
            slot_type = sample_slot.slot_type.upper()

            # Skip recorder slots (129-136)
            if slot_num >= RECORDER_SLOTS_START:
                continue

            if slot_type == "FLEX":
                self._flex_slots[path] = slot_num
            elif slot_type == "STATIC":
                self._static_slots[path] = slot_num

    @classmethod
    def from_zip(cls, zip_path: Path) -> "Project":
        """
        Load a project from a zip file.

        Args:
            zip_path: Path to project zip file

        Returns:
            Project instance
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            unzip_project(zip_path, tmp_path)
            project = cls.from_directory(tmp_path)
            project.name = Path(zip_path).stem.upper()
            return project

    def to_directory(self, path: Path) -> None:
        """
        Save the project to a directory.

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

        # Save bank files
        for bank_num, bank_file in self._bank_files.items():
            bank_file.to_file(path / f"bank{bank_num:02d}.work")

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
    def settings(self) -> ProjectSettings:
        """Get project settings."""
        return self._project_file.settings

    @property
    def tempo(self) -> float:
        """Get the project tempo in BPM."""
        return self._project_file.tempo

    @tempo.setter
    def tempo(self, bpm: float):
        """Set the project tempo in BPM."""
        self._project_file.tempo = bpm

    # === Sample management ===

    def _next_available_slot(self, slot_type: str) -> int:
        """
        Find the next available slot for a sample type.

        Args:
            slot_type: "FLEX" or "STATIC"

        Returns:
            Next available slot number (1-128)

        Raises:
            SlotLimitExceeded: If all 128 slots are used
        """
        is_flex = slot_type.upper() == "FLEX"
        used_slots = set(self._flex_slots.values()) if is_flex else set(self._static_slots.values())
        max_slots = MAX_FLEX_SAMPLE_SLOTS if is_flex else MAX_STATIC_SAMPLE_SLOTS

        for slot in range(1, max_slots + 1):
            if slot not in used_slots:
                return slot

        raise SlotLimitExceeded(
            f"All {max_slots} {slot_type.lower()} sample slots are in use"
        )

    def _update_flex_count(self) -> None:
        """Update flex_count in all loaded banks."""
        flex_count = len(self._flex_slots)
        for bank_file in self._bank_files.values():
            bank_file.flex_count = flex_count

    def add_sample(
        self,
        path: str,
        wav_path: Path = None,
        slot_type: str = "FLEX",
        slot: Optional[int] = None,
        gain: int = 48,
    ) -> SampleSlot:
        """
        Add a sample to a slot.

        If the same path has already been added, returns the existing slot.
        If no slot is specified, automatically assigns the next available slot.

        Args:
            path: Relative path for Octatrack (e.g., "../AUDIO/kick.wav")
            wav_path: Optional local path to WAV file for reading frame count
            slot_type: "FLEX" or "STATIC"
            slot: Slot number (1-128). If None, auto-assigns next available.
            gain: Gain value 0-127 (48 = 0dB)

        Returns:
            The created (or existing) SampleSlot

        Raises:
            SlotLimitExceeded: If all 128 slots for this type are in use
            InvalidSlotNumber: If explicit slot number is out of range
        """
        is_flex = slot_type.upper() == "FLEX"
        slot_dict = self._flex_slots if is_flex else self._static_slots
        max_slots = MAX_FLEX_SAMPLE_SLOTS if is_flex else MAX_STATIC_SAMPLE_SLOTS

        # Check if this path already has a slot assigned
        if path in slot_dict:
            existing_slot = slot_dict[path]
            # Return the existing sample slot
            for ss in self._project_file.sample_slots:
                if ss.slot_number == existing_slot and ss.slot_type.upper() == slot_type.upper():
                    return ss

        # Validate or auto-assign slot
        if slot is None:
            slot = self._next_available_slot(slot_type)
        else:
            if slot < 1 or slot > max_slots:
                raise InvalidSlotNumber(
                    f"Slot {slot} is out of range. Valid range is 1-{max_slots} for {slot_type.lower()} samples."
                )
            # Check if slot is already in use (by a different path)
            used_slots = set(slot_dict.values())
            if slot in used_slots:
                # Find which path is using it
                for existing_path, existing_slot in slot_dict.items():
                    if existing_slot == slot:
                        raise InvalidSlotNumber(
                            f"Slot {slot} is already in use by '{existing_path}'"
                        )

        # Add to project.work
        sample_slot = self._project_file.add_sample_slot(
            slot_number=slot,
            path=path,
            slot_type=slot_type,
            gain=gain,
        )

        # Track the slot
        slot_dict[path] = slot

        # Update markers.work with sample length if WAV path provided
        if wav_path:
            frame_count = _get_wav_frame_count(wav_path)
            if frame_count > 0:
                is_static = slot_type.upper() == "STATIC"
                self.markers.set_sample_length(slot, frame_count, is_static)

        # Auto-update flex_count in banks
        if is_flex:
            self._update_flex_count()

        return sample_slot

    def get_slot(self, path: str, slot_type: str = "FLEX") -> Optional[int]:
        """
        Get the slot number assigned to a sample path.

        Args:
            path: The sample path
            slot_type: "FLEX" or "STATIC"

        Returns:
            Slot number if found, None otherwise
        """
        slot_dict = self._flex_slots if slot_type.upper() == "FLEX" else self._static_slots
        return slot_dict.get(path)

    @property
    def flex_slot_count(self) -> int:
        """Number of flex sample slots in use."""
        return len(self._flex_slots)

    @property
    def static_slot_count(self) -> int:
        """Number of static sample slots in use."""
        return len(self._static_slots)

    @property
    def sample_paths(self) -> list:
        """List of all sample paths (flex and static) in the project."""
        return list(self._flex_slots.keys()) + list(self._static_slots.keys())

    def add_recorder_slots(self) -> None:
        """Add the 8 recorder buffer slots (129-136)."""
        self._project_file.add_recorder_slots()


def _get_wav_frame_count(wav_path: Path) -> int:
    """Get the number of audio frames in a WAV file."""
    import wave

    try:
        with wave.open(str(wav_path), 'rb') as w:
            return w.getnframes()
    except Exception:
        return 0
