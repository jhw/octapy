"""
Project file I/O for Octatrack.

The project file (project.work) is a text-based INI-style file containing:
- Project metadata (type, version, OS version)
- Project settings (tempo, MIDI config, mixer, etc.)
- Project state (current bank, pattern, etc.)
- Sample slot assignments

IMPORTANT: project.work uses CRLF line endings (\\r\\n), not LF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SampleSlot:
    """
    A sample slot assignment in the project.

    Slots 1-128 are for user samples.
    Slots 129-136 are for recorder buffers.
    """
    slot_type: str = "FLEX"     # FLEX or STATIC
    slot_number: int = 1        # 1-indexed (1-128 for samples, 129-136 for recorders)
    path: str = ""              # Relative path from project folder
    bpm_x24: int = 2880         # BPM * 24 (2880 = 120 BPM)
    timestretch_mode: int = 0   # 0 = OFF, 2 = NORMAL, 3 = BEAT
    loop_mode: int = 0          # 0 = OFF, 1 = LOOP, 2 = PIPO
    gain: int = 72              # 0-96, ±24dB in 0.5dB steps (72 = 0dB)
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
    """
    Project-level settings written to the [SETTINGS] section of project.work.

    Fields are listed in the order they appear in the file.
    """
    # Basic
    write_protected: int = 0
    tempo_x24: int = 2880       # BPM * 24 (2880 = 120 BPM)
    pattern_tempo_enabled: int = 0
    # MIDI clock / transport / program change
    midi_clock_send: int = 0
    midi_clock_receive: int = 0
    midi_transport_send: int = 0
    midi_transport_receive: int = 0
    midi_program_change_send: int = 0
    midi_program_change_send_ch: int = -1
    midi_program_change_receive: int = 0
    midi_program_change_receive_ch: int = -1
    # MIDI trig channels (per MIDI track 1-8)
    midi_trig_channels: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6, 7])
    # MIDI control / routing
    midi_auto_channel: int = 10
    midi_soft_thru: int = 0
    midi_audio_trk_cc_in: int = 1
    midi_audio_trk_cc_out: int = 3
    midi_audio_trk_note_in: int = 1
    midi_audio_trk_note_out: int = 3
    midi_midi_trk_cc_in: int = 1
    # Pattern change
    pattern_change_chain_behavior: int = 0
    pattern_change_auto_silence_tracks: int = 0
    pattern_change_auto_trig_lfos: int = 0
    # Memory/recorder
    load_24bit_flex: int = 0
    dynamic_recorders: int = 0
    record_24bit: int = 0
    reserved_recorder_count: int = 8
    reserved_recorder_length: int = 16
    # Mixer/Input
    input_delay_compensation: int = 0
    gate_ab: int = 127
    gate_cd: int = 127
    gain_ab: int = 64
    gain_cd: int = 64
    dir_ab: int = 0
    dir_cd: int = 0
    phones_mix: int = 64
    main_to_cue: int = 0
    master_track: int = 0       # 0 = disabled, 1 = track 8 is master
    cue_studio_mode: int = 0
    main_level: int = 64
    cue_level: int = 64
    # Metronome
    metronome_time_signature: int = 3
    metronome_time_signature_denominator: int = 2
    metronome_preroll: int = 0
    metronome_cue_volume: int = 32
    metronome_main_volume: int = 0
    metronome_pitch: int = 12
    metronome_tonal: int = 1
    metronome_enabled: int = 0
    # Trig mode (per MIDI track 1-8)
    trig_mode_midi: List[int] = field(default_factory=lambda: [0] * 8)


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


# =============================================================================
# Settings field schema
#
# Drives both parsing and serialization for the SETTINGS section so the two
# stay in lock-step. Each entry is (ini_key, settings_attr). The order here
# matches the order in the project.work file.
# =============================================================================

_SETTINGS_FIELDS = (
    ("WRITEPROTECTED", "write_protected"),
    ("TEMPOx24", "tempo_x24"),
    ("PATTERN_TEMPO_ENABLED", "pattern_tempo_enabled"),
    ("MIDI_CLOCK_SEND", "midi_clock_send"),
    ("MIDI_CLOCK_RECEIVE", "midi_clock_receive"),
    ("MIDI_TRANSPORT_SEND", "midi_transport_send"),
    ("MIDI_TRANSPORT_RECEIVE", "midi_transport_receive"),
    ("MIDI_PROGRAM_CHANGE_SEND", "midi_program_change_send"),
    ("MIDI_PROGRAM_CHANGE_SEND_CH", "midi_program_change_send_ch"),
    ("MIDI_PROGRAM_CHANGE_RECEIVE", "midi_program_change_receive"),
    ("MIDI_PROGRAM_CHANGE_RECEIVE_CH", "midi_program_change_receive_ch"),
    # MIDI_TRIG_CH1..8 handled separately as a list
    ("MIDI_AUTO_CHANNEL", "midi_auto_channel"),
    ("MIDI_SOFT_THRU", "midi_soft_thru"),
    ("MIDI_AUDIO_TRK_CC_IN", "midi_audio_trk_cc_in"),
    ("MIDI_AUDIO_TRK_CC_OUT", "midi_audio_trk_cc_out"),
    ("MIDI_AUDIO_TRK_NOTE_IN", "midi_audio_trk_note_in"),
    ("MIDI_AUDIO_TRK_NOTE_OUT", "midi_audio_trk_note_out"),
    ("MIDI_MIDI_TRK_CC_IN", "midi_midi_trk_cc_in"),
    ("PATTERN_CHANGE_CHAIN_BEHAVIOR", "pattern_change_chain_behavior"),
    ("PATTERN_CHANGE_AUTO_SILENCE_TRACKS", "pattern_change_auto_silence_tracks"),
    ("PATTERN_CHANGE_AUTO_TRIG_LFOS", "pattern_change_auto_trig_lfos"),
    ("LOAD_24BIT_FLEX", "load_24bit_flex"),
    ("DYNAMIC_RECORDERS", "dynamic_recorders"),
    ("RECORD_24BIT", "record_24bit"),
    ("RESERVED_RECORDER_COUNT", "reserved_recorder_count"),
    ("RESERVED_RECORDER_LENGTH", "reserved_recorder_length"),
    ("INPUT_DELAY_COMPENSATION", "input_delay_compensation"),
    ("GATE_AB", "gate_ab"),
    ("GATE_CD", "gate_cd"),
    ("GAIN_AB", "gain_ab"),
    ("GAIN_CD", "gain_cd"),
    ("DIR_AB", "dir_ab"),
    ("DIR_CD", "dir_cd"),
    ("PHONES_MIX", "phones_mix"),
    ("MAIN_TO_CUE", "main_to_cue"),
    ("MASTER_TRACK", "master_track"),
    ("CUE_STUDIO_MODE", "cue_studio_mode"),
    ("MAIN_LEVEL", "main_level"),
    ("CUE_LEVEL", "cue_level"),
    ("METRONOME_TIME_SIGNATURE", "metronome_time_signature"),
    ("METRONOME_TIME_SIGNATURE_DENOMINATOR", "metronome_time_signature_denominator"),
    ("METRONOME_PREROLL", "metronome_preroll"),
    ("METRONOME_CUE_VOLUME", "metronome_cue_volume"),
    ("METRONOME_MAIN_VOLUME", "metronome_main_volume"),
    ("METRONOME_PITCH", "metronome_pitch"),
    ("METRONOME_TONAL", "metronome_tonal"),
    ("METRONOME_ENABLED", "metronome_enabled"),
    # TRIG_MODE_MIDI x8 handled separately as a list
)

# Insertion point for MIDI_TRIG_CH1..8 (after MIDI_PROGRAM_CHANGE_RECEIVE_CH)
_MIDI_TRIG_CH_AFTER = "MIDI_PROGRAM_CHANGE_RECEIVE_CH"


_STATE_FIELDS = (
    ("BANK", "bank"),
    ("PATTERN", "pattern"),
    ("ARRANGEMENT", "arrangement"),
    ("ARRANGEMENT_MODE", "arrangement_mode"),
    ("PART", "part"),
    ("TRACK", "track"),
    ("TRACK_OTHERMODE", "track_othermode"),
    ("SCENE_A_MUTE", "scene_a_mute"),
    ("SCENE_B_MUTE", "scene_b_mute"),
    ("TRACK_CUE_MASK", "track_cue_mask"),
    ("TRACK_MUTE_MASK", "track_mute_mask"),
    ("TRACK_SOLO_MASK", "track_solo_mask"),
    ("MIDI_TRACK_MUTE_MASK", "midi_track_mute_mask"),
    ("MIDI_TRACK_SOLO_MASK", "midi_track_solo_mask"),
    ("MIDI_MODE", "midi_mode"),
)


# =============================================================================
# ProjectFile Class
# =============================================================================

@dataclass
class ProjectFile:
    """
    Low-level Octatrack project file I/O (project.work).

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

    @classmethod
    def new(cls) -> "ProjectFile":
        """Create a new ProjectFile from the embedded template."""
        data = read_template_file("project.work")
        content = data.decode('utf-8')
        project = cls()
        project._parse_content(content)
        return project

    def _parse_content(self, content: str) -> None:
        """Parse the INI-style content."""
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

        # Parse SETTINGS section
        settings_match = re.search(r'\[SETTINGS\](.*?)\[/SETTINGS\]', content, re.DOTALL)
        if settings_match:
            self._parse_settings(settings_match.group(1))

        # Parse STATES section
        states_match = re.search(r'\[STATES\](.*?)\[/STATES\]', content, re.DOTALL)
        if states_match:
            self._parse_state(states_match.group(1))

        # Parse SAMPLE sections
        sample_matches = re.findall(r'\[SAMPLE\](.*?)\[/SAMPLE\]', content, re.DOTALL)
        for sample_content in sample_matches:
            self.sample_slots.append(self._parse_sample(sample_content))

    def _parse_settings(self, content: str) -> None:
        """Parse the SETTINGS section body and populate self.settings."""
        for ini_key, attr in _SETTINGS_FIELDS:
            value = _read_int(content, ini_key)
            if value is not None:
                setattr(self.settings, attr, value)

        # MIDI_TRIG_CH1..8 — array of 8 channels
        for i in range(8):
            value = _read_int(content, f"MIDI_TRIG_CH{i+1}")
            if value is not None:
                self.settings.midi_trig_channels[i] = value

        # TRIG_MODE_MIDI x8 — duplicate-key array. Take the values in order.
        trig_modes = [int(m) for m in re.findall(r'^TRIG_MODE_MIDI=(-?\d+)', content, re.MULTILINE)]
        for i, v in enumerate(trig_modes[:8]):
            self.settings.trig_mode_midi[i] = v

    def _parse_state(self, content: str) -> None:
        """Parse the STATES section body and populate self.state."""
        for ini_key, attr in _STATE_FIELDS:
            value = _read_int(content, ini_key)
            if value is not None:
                setattr(self.state, attr, value)

    def _parse_sample(self, content: str) -> SampleSlot:
        """Parse a single [SAMPLE] block into a SampleSlot."""
        slot = SampleSlot()

        type_match = re.search(r'TYPE=(\w+)', content)
        if type_match:
            slot.slot_type = type_match.group(1)

        for ini_key, attr, kind in (
            ("SLOT", "slot_number", int),
            ("BPMx24", "bpm_x24", int),
            ("TSMODE", "timestretch_mode", int),
            ("LOOPMODE", "loop_mode", int),
            ("GAIN", "gain", int),
            ("TRIGQUANTIZATION", "trig_quantization", int),
        ):
            value = _read_int(content, ini_key)
            if value is not None:
                setattr(slot, attr, value)

        path_match = re.search(r'^PATH=(.*)$', content, re.MULTILINE)
        if path_match:
            slot.path = path_match.group(1).strip()

        return slot

    def to_file(self, path: Path) -> None:
        """Write the project file to disk with CRLF line endings."""
        content = self._generate_content()
        content_crlf = content.replace('\n', '\r\n')

        with open(path, 'wb') as f:
            f.write(content_crlf.encode('utf-8'))

    def _generate_content(self) -> str:
        """Generate the INI-style content."""
        lines: List[str] = []

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
        for ini_key, attr in _SETTINGS_FIELDS:
            lines.append(f"{ini_key}={getattr(self.settings, attr)}")
            if ini_key == _MIDI_TRIG_CH_AFTER:
                for i, ch in enumerate(self.settings.midi_trig_channels):
                    lines.append(f"MIDI_TRIG_CH{i+1}={ch}")
        # TRIG_MODE_MIDI x8 at the end of SETTINGS
        for v in self.settings.trig_mode_midi:
            lines.append(f"TRIG_MODE_MIDI={v}")
        lines.append("[/SETTINGS]")
        lines.append("")

        # STATES section
        lines.append("############################")
        lines.append("# Project States")
        lines.append("############################")
        lines.append("")
        lines.append("[STATES]")
        for ini_key, attr in _STATE_FIELDS:
            lines.append(f"{ini_key}={getattr(self.state, attr)}")
        lines.append("[/STATES]")
        lines.append("")

        # SAMPLES section
        lines.append("############################")
        lines.append("# Samples")
        lines.append("############################")
        lines.append("")

        # Reference writes all STATIC slots before all FLEX slots (each type
        # sorted by slot number within its own block).
        for slot in sorted(self.sample_slots, key=lambda s: (s.slot_type != "STATIC", s.slot_number)):
            lines.append(slot.to_ini_block())

        lines.append("############################")
        lines.append("")
        lines.append("")

        return '\n'.join(lines)

    def add_sample_slot(
        self,
        slot_number: int,
        path: str,
        slot_type: str = "FLEX",
        gain: int = 72,
        loop_mode: int = 0,
        timestretch_mode: int = 0,
    ) -> SampleSlot:
        """Add a sample to a slot."""
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
                timestretch_mode=2,
                loop_mode=0,
                gain=72,
                trig_quantization=-1,
            )
            self.sample_slots.append(slot)

    @property
    def tempo(self) -> float:
        """Get the project tempo in BPM."""
        return self.settings.tempo_x24 / 24.0

    @tempo.setter
    def tempo(self, bpm: float):
        """Set the project tempo in BPM."""
        self.settings.tempo_x24 = int(bpm * 24)

    @property
    def tempo_x24(self) -> int:
        """Get the raw tempo value (BPM * 24)."""
        return self.settings.tempo_x24

    @tempo_x24.setter
    def tempo_x24(self, value: int):
        """Set the raw tempo value (BPM * 24)."""
        self.settings.tempo_x24 = value


def _read_int(content: str, key: str) -> "int | None":
    """Read an integer value for INI key from content.

    Matches `KEY=value` at start of line, with a signed integer value.
    """
    m = re.search(rf'^{re.escape(key)}=(-?\d+)\s*$', content, re.MULTILINE)
    if m is None:
        return None
    return int(m.group(1))


# =============================================================================
# Project zip/unzip utilities
# =============================================================================

def zip_project(project_dir: Path, zip_path: Path, audio_subdir: str = "projects") -> None:
    """Zip a project directory into a single archive.

    The project name (directory name) is used as the zip prefix,
    so the archive extracts directly to a named project folder.

    Structure:
        {project_name}/                          - .work files
        AUDIO/{audio_subdir}/{project_name}/     - .wav files

    The audio_subdir must match the subdir used when adding samples
    (Project._audio_subdir), so that paths in project.work resolve
    correctly on the Octatrack.
    """
    import zipfile

    project_name = project_dir.name

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.work':
                zf.write(file_path, f"{project_name}/{file_path.name}")

        # Include samples/ directory if present
        samples_dir = project_dir / "samples"
        if samples_dir.exists():
            for sample_file in samples_dir.glob("*.wav"):
                zf.write(sample_file, f"AUDIO/{audio_subdir}/{project_name}/{sample_file.name}")


def unzip_project(zip_path: Path, dest_dir: Path) -> None:
    """Unzip a project archive to a directory."""
    import zipfile

    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest_dir)


# =============================================================================
# Template utilities
# =============================================================================

DEFAULT_TEMPLATE = "project-template-1.40B.zip"


def _get_template_zip(name: str = DEFAULT_TEMPLATE):
    """Get a ZipFile handle to an embedded template."""
    import zipfile
    from importlib.resources import files

    template_path = files('octapy.templates').joinpath(name)
    return zipfile.ZipFile(template_path, 'r')


def read_template_file(filename: str, template: str = DEFAULT_TEMPLATE) -> bytes:
    """Read a single file from an embedded template zip."""
    with _get_template_zip(template) as zf:
        return zf.read(filename)


def extract_template(dest_dir: Path, template: str = DEFAULT_TEMPLATE) -> None:
    """Extract a complete project template to a directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    with _get_template_zip(template) as zf:
        zf.extractall(dest_dir)
