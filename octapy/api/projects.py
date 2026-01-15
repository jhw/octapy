"""
Project file types and I/O for Octatrack.

The project file (project.work) is a text-based INI-style file containing:
- Project metadata (type, version, OS version)
- Project settings (tempo, MIDI config, mixer, etc.)
- Project state (current bank, pattern, etc.)
- Sample slot assignments

IMPORTANT: project.work uses CRLF line endings (\\r\\n), not LF.

Ported from ot-tools-io (Rust).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import re


@dataclass
class SampleSlot:
    """
    A sample slot assignment in the project.

    Slots 1-128 are for user samples.
    Slots 129-136 are for recorder buffers.
    """
    slot_type: str = "FLEX"     # FLEX or STATIC
    slot_number: int = 1        # 1-indexed (1-128 for samples, 129-136 for recorders)
    path: str = ""              # Relative path from project folder (e.g., "../AUDIO/sample.wav")
    bpm_x24: int = 2880         # BPM * 24 (2880 = 120 BPM)
    timestretch_mode: int = 0   # 0 = OFF, 1 = NORMAL, 2 = BEAT
    loop_mode: int = 0          # 0 = OFF, 1 = LOOP, 2 = PIPO
    gain: int = 48              # 0-127 (48 = 0dB)
    trig_quantization: int = -1 # -1 = default

    def to_ini_block(self) -> str:
        """Convert to INI block format."""
        return f"""[SAMPLE]
TYPE={self.slot_type}
SLOT={self.slot_number:03d}
PATH={self.path}
BPMx24={self.bpm_x24}
TSMODE={self.timestretch_mode}
LOOPMODE={self.loop_mode}
GAIN={self.gain}
TRIGQUANTIZATION={self.trig_quantization}
[/SAMPLE]
"""


@dataclass
class ProjectSettings:
    """Project-level settings."""
    write_protected: int = 0
    tempo_x24: int = 2880       # BPM * 24 (2880 = 120 BPM)
    pattern_tempo_enabled: int = 0
    midi_clock_send: int = 0
    midi_clock_receive: int = 0
    midi_transport_send: int = 0
    midi_transport_receive: int = 0
    midi_program_change_send: int = 0
    midi_program_change_send_ch: int = -1
    midi_program_change_receive: int = 0
    midi_program_change_receive_ch: int = -1
    load_24bit_flex: int = 0
    dynamic_recorders: int = 0
    record_24bit: int = 0
    reserved_recorder_count: int = 8
    reserved_recorder_length: int = 16
    # Many more settings exist - these are the essentials


@dataclass
class ProjectState:
    """Current project state (bank, pattern, track, etc.)."""
    bank: int = 0
    pattern: int = 0
    arrangement: int = 0
    arrangement_mode: int = 0
    part: int = 0
    track: int = 0
    track_othermode: int = 0
    scene_a_mute: int = 0
    scene_b_mute: int = 0
    track_cue_mask: int = 0
    track_mute_mask: int = 0
    track_solo_mask: int = 0
    midi_track_mute_mask: int = 0
    midi_track_solo_mask: int = 0
    midi_mode: int = 0


@dataclass
class ProjectFile:
    """
    Octatrack project file (project.work).

    This is a text-based INI-style file with CRLF line endings.
    """
    os_version: str = "R0177     1.40B"
    version: int = 19
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    state: ProjectState = field(default_factory=ProjectState)
    sample_slots: List[SampleSlot] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> "ProjectFile":
        """Load a project file from disk."""
        with open(path, 'rb') as f:
            content = f.read().decode('utf-8')

        project = cls()
        project._parse_content(content)
        return project

    def _parse_content(self, content: str) -> None:
        """Parse the INI-style content."""
        # Normalize line endings
        content = content.replace('\r\n', '\n')

        # Parse META section
        meta_match = re.search(r'\[META\](.*?)\[/META\]', content, re.DOTALL)
        if meta_match:
            meta_content = meta_match.group(1)
            version_match = re.search(r'VERSION=(\d+)', meta_content)
            if version_match:
                self.version = int(version_match.group(1))
            os_match = re.search(r'OS_VERSION=(.+)', meta_content)
            if os_match:
                self.os_version = os_match.group(1).strip()

        # Parse SAMPLE sections
        sample_matches = re.findall(r'\[SAMPLE\](.*?)\[/SAMPLE\]', content, re.DOTALL)
        for sample_content in sample_matches:
            slot = SampleSlot()

            type_match = re.search(r'TYPE=(\w+)', sample_content)
            if type_match:
                slot.slot_type = type_match.group(1)

            slot_match = re.search(r'SLOT=(\d+)', sample_content)
            if slot_match:
                slot.slot_number = int(slot_match.group(1))

            path_match = re.search(r'PATH=(.+)', sample_content)
            if path_match:
                slot.path = path_match.group(1).strip()

            gain_match = re.search(r'GAIN=(\d+)', sample_content)
            if gain_match:
                slot.gain = int(gain_match.group(1))

            self.sample_slots.append(slot)

    def to_file(self, path: Path) -> None:
        """Write the project file to disk with CRLF line endings."""
        content = self._generate_content()
        # Convert to CRLF
        content_crlf = content.replace('\n', '\r\n')

        with open(path, 'wb') as f:
            f.write(content_crlf.encode('utf-8'))

    def _generate_content(self) -> str:
        """Generate the INI-style content."""
        lines = []

        # Header comment
        lines.append("############################")
        lines.append("# Project Settings")
        lines.append("############################")
        lines.append("")

        # META section
        lines.append("[META]")
        lines.append("TYPE=OCTATRACK DPS-1 PROJECT")
        lines.append(f"VERSION={self.version}")
        lines.append(f"OS_VERSION={self.os_version}")
        lines.append("[/META]")
        lines.append("")

        # SETTINGS section
        lines.append("[SETTINGS]")
        lines.append(f"WRITEPROTECTED={self.settings.write_protected}")
        lines.append(f"TEMPOx24={self.settings.tempo_x24}")
        lines.append(f"PATTERN_TEMPO_ENABLED={self.settings.pattern_tempo_enabled}")
        lines.append(f"MIDI_CLOCK_SEND={self.settings.midi_clock_send}")
        lines.append(f"MIDI_CLOCK_RECEIVE={self.settings.midi_clock_receive}")
        lines.append(f"MIDI_TRANSPORT_SEND={self.settings.midi_transport_send}")
        lines.append(f"MIDI_TRANSPORT_RECEIVE={self.settings.midi_transport_receive}")
        lines.append(f"MIDI_PROGRAM_CHANGE_SEND={self.settings.midi_program_change_send}")
        lines.append(f"MIDI_PROGRAM_CHANGE_SEND_CH={self.settings.midi_program_change_send_ch}")
        lines.append(f"MIDI_PROGRAM_CHANGE_RECEIVE={self.settings.midi_program_change_receive}")
        lines.append(f"MIDI_PROGRAM_CHANGE_RECEIVE_CH={self.settings.midi_program_change_receive_ch}")

        # MIDI trig channels (0-7 for tracks 1-8)
        for i in range(8):
            lines.append(f"MIDI_TRIG_CH{i+1}={i}")

        lines.append("MIDI_AUTO_CHANNEL=10")
        lines.append("MIDI_SOFT_THRU=0")
        lines.append("MIDI_AUDIO_TRK_CC_IN=1")
        lines.append("MIDI_AUDIO_TRK_CC_OUT=3")
        lines.append("MIDI_AUDIO_TRK_NOTE_IN=1")
        lines.append("MIDI_AUDIO_TRK_NOTE_OUT=3")
        lines.append("MIDI_MIDI_TRK_CC_IN=1")
        lines.append("PATTERN_CHANGE_CHAIN_BEHAVIOR=0")
        lines.append("PATTERN_CHANGE_AUTO_SILENCE_TRACKS=0")
        lines.append("PATTERN_CHANGE_AUTO_TRIG_LFOS=0")
        lines.append(f"LOAD_24BIT_FLEX={self.settings.load_24bit_flex}")
        lines.append(f"DYNAMIC_RECORDERS={self.settings.dynamic_recorders}")
        lines.append(f"RECORD_24BIT={self.settings.record_24bit}")
        lines.append(f"RESERVED_RECORDER_COUNT={self.settings.reserved_recorder_count}")
        lines.append(f"RESERVED_RECORDER_LENGTH={self.settings.reserved_recorder_length}")
        lines.append("INPUT_DELAY_COMPENSATION=0")
        lines.append("GATE_AB=127")
        lines.append("GATE_CD=127")
        lines.append("GAIN_AB=64")
        lines.append("GAIN_CD=64")
        lines.append("DIR_AB=0")
        lines.append("DIR_CD=0")
        lines.append("PHONES_MIX=64")
        lines.append("MAIN_TO_CUE=0")
        lines.append("MASTER_TRACK=0")
        lines.append("CUE_STUDIO_MODE=0")
        lines.append("MAIN_LEVEL=64")
        lines.append("CUE_LEVEL=64")
        lines.append("METRONOME_TIME_SIGNATURE=3")
        lines.append("METRONOME_TIME_SIGNATURE_DENOMINATOR=2")
        lines.append("METRONOME_PREROLL=0")
        lines.append("METRONOME_CUE_VOLUME=32")
        lines.append("METRONOME_MAIN_VOLUME=0")
        lines.append("METRONOME_PITCH=12")
        lines.append("METRONOME_TONAL=1")
        lines.append("METRONOME_ENABLED=0")

        # TRIG_MODE_MIDI appears 8 times
        for _ in range(8):
            lines.append("TRIG_MODE_MIDI=0")

        lines.append("[/SETTINGS]")
        lines.append("")

        # STATES section
        lines.append("############################")
        lines.append("# Project States")
        lines.append("############################")
        lines.append("")
        lines.append("[STATES]")
        lines.append(f"BANK={self.state.bank}")
        lines.append(f"PATTERN={self.state.pattern}")
        lines.append(f"ARRANGEMENT={self.state.arrangement}")
        lines.append(f"ARRANGEMENT_MODE={self.state.arrangement_mode}")
        lines.append(f"PART={self.state.part}")
        lines.append(f"TRACK={self.state.track}")
        lines.append(f"TRACK_OTHERMODE={self.state.track_othermode}")
        lines.append(f"SCENE_A_MUTE={self.state.scene_a_mute}")
        lines.append(f"SCENE_B_MUTE={self.state.scene_b_mute}")
        lines.append(f"TRACK_CUE_MASK={self.state.track_cue_mask}")
        lines.append(f"TRACK_MUTE_MASK={self.state.track_mute_mask}")
        lines.append(f"TRACK_SOLO_MASK={self.state.track_solo_mask}")
        lines.append(f"MIDI_TRACK_MUTE_MASK={self.state.midi_track_mute_mask}")
        lines.append(f"MIDI_TRACK_SOLO_MASK={self.state.midi_track_solo_mask}")
        lines.append(f"MIDI_MODE={self.state.midi_mode}")
        lines.append("[/STATES]")
        lines.append("")

        # SAMPLES section
        lines.append("############################")
        lines.append("# Samples")
        lines.append("############################")
        lines.append("")

        # Add user sample slots
        for slot in self.sample_slots:
            lines.append(slot.to_ini_block())

        lines.append("############################")
        lines.append("")

        return '\n'.join(lines)

    def add_sample_slot(
        self,
        slot_number: int,
        path: str,
        slot_type: str = "FLEX",
        gain: int = 48,
        loop_mode: int = 0,
        timestretch_mode: int = 0,
    ) -> SampleSlot:
        """
        Add a sample to a slot.

        Args:
            slot_number: Slot number (1-128 for samples, 129-136 for recorders)
            path: Relative path to sample (e.g., "../AUDIO/sample.wav")
            slot_type: "FLEX" or "STATIC"
            gain: Gain value 0-127 (48 = 0dB)
            loop_mode: 0 = OFF, 1 = LOOP, 2 = PIPO
            timestretch_mode: 0 = OFF, 1 = NORMAL, 2 = BEAT

        Returns:
            The created SampleSlot
        """
        slot = SampleSlot(
            slot_type=slot_type,
            slot_number=slot_number,
            path=path,
            gain=gain,
            loop_mode=loop_mode,
            timestretch_mode=timestretch_mode,
        )
        self.sample_slots.append(slot)
        return slot

    def add_recorder_slots(self) -> None:
        """Add the 8 recorder buffer slots (129-136)."""
        for i in range(8):
            slot = SampleSlot(
                slot_type="FLEX",
                slot_number=129 + i,
                path="",
                bpm_x24=2880,
                timestretch_mode=2,  # BEAT mode for recorders
                loop_mode=0,
                gain=72,
                trig_quantization=-1,
            )
            self.sample_slots.append(slot)

    # === Tempo accessors ===

    @property
    def tempo(self) -> float:
        """
        Get the project tempo in BPM.

        Returns:
            Tempo in BPM (e.g., 120.0)
        """
        return self.settings.tempo_x24 / 24.0

    @tempo.setter
    def tempo(self, bpm: float):
        """
        Set the project tempo in BPM.

        Args:
            bpm: Tempo in BPM (e.g., 120.0)
        """
        self.settings.tempo_x24 = int(bpm * 24)

    @property
    def tempo_x24(self) -> int:
        """
        Get the raw tempo value (BPM * 24).

        Returns:
            Raw tempo value (e.g., 2880 for 120 BPM)
        """
        return self.settings.tempo_x24

    @tempo_x24.setter
    def tempo_x24(self, value: int):
        """
        Set the raw tempo value (BPM * 24).

        Args:
            value: Raw tempo value (e.g., 2880 for 120 BPM)
        """
        self.settings.tempo_x24 = value


# === Project zip/unzip utilities ===

def zip_project(project_dir: Path, zip_path: Path) -> None:
    """
    Zip a project directory into a single archive.

    Args:
        project_dir: Path to project directory containing .work files
        zip_path: Path for output zip file
    """
    import zipfile

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.work':
                zf.write(file_path, file_path.name)


def unzip_project(zip_path: Path, dest_dir: Path) -> None:
    """
    Unzip a project archive to a directory.

    Args:
        zip_path: Path to project zip file
        dest_dir: Destination directory (will be created if needed)
    """
    import zipfile

    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest_dir)


# === Template utilities ===

# Default template for OS 1.40B
DEFAULT_TEMPLATE = "project-template-1.40B.zip"


def _get_template_zip(name: str = DEFAULT_TEMPLATE):
    """Get a ZipFile handle to an embedded template."""
    import zipfile
    from importlib.resources import files

    template_path = files('octapy.templates').joinpath(name)
    return zipfile.ZipFile(template_path, 'r')


def read_template_file(filename: str, template: str = DEFAULT_TEMPLATE) -> bytes:
    """
    Read a single file from an embedded template zip.

    Args:
        filename: File to read (e.g., 'bank01.work', 'markers.work')
        template: Template zip name (default: project-template-1.40B.zip)

    Returns:
        File contents as bytes
    """
    with _get_template_zip(template) as zf:
        return zf.read(filename)


def extract_template(dest_dir: Path, template: str = DEFAULT_TEMPLATE) -> None:
    """
    Extract a complete project template to a directory.

    Args:
        dest_dir: Destination directory (will be created if needed)
        template: Template zip name (default: project-template-1.40B.zip)
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    with _get_template_zip(template) as zf:
        zf.extractall(dest_dir)
