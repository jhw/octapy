"""
Settings class - project-level settings.
"""

from __future__ import annotations

from .._io import ProjectSettings as _ProjectSettings


class Settings:
    """
    High-level representation of project settings.

    Wraps the low-level ProjectSettings dataclass with typed accessors.
    Access via project.settings.

    Usage:
        project.settings.tempo = 140.0
        project.settings.midi_clock_send = True
        project.settings.record_24bit = True
    """

    def __init__(self, project_settings: _ProjectSettings):
        """
        Internal constructor. Access via project.settings.

        Args:
            project_settings: Low-level ProjectSettings dataclass
        """
        self._settings = project_settings

    # === Tempo ===

    @property
    def tempo(self) -> float:
        """Get/set the project tempo in BPM."""
        return self._settings.tempo_x24 / 24.0

    @tempo.setter
    def tempo(self, bpm: float):
        self._settings.tempo_x24 = int(bpm * 24)

    # === MIDI Clock/Transport ===

    @property
    def midi_clock_send(self) -> bool:
        """Enable/disable sending MIDI clock to external gear."""
        return bool(self._settings.midi_clock_send)

    @midi_clock_send.setter
    def midi_clock_send(self, value: bool):
        self._settings.midi_clock_send = int(value)

    @property
    def midi_clock_receive(self) -> bool:
        """Enable/disable syncing to incoming MIDI clock."""
        return bool(self._settings.midi_clock_receive)

    @midi_clock_receive.setter
    def midi_clock_receive(self, value: bool):
        self._settings.midi_clock_receive = int(value)

    @property
    def midi_transport_send(self) -> bool:
        """Enable/disable sending MIDI transport (start/stop/continue)."""
        return bool(self._settings.midi_transport_send)

    @midi_transport_send.setter
    def midi_transport_send(self, value: bool):
        self._settings.midi_transport_send = int(value)

    @property
    def midi_transport_receive(self) -> bool:
        """Enable/disable responding to MIDI transport (start/stop/continue)."""
        return bool(self._settings.midi_transport_receive)

    @midi_transport_receive.setter
    def midi_transport_receive(self, value: bool):
        self._settings.midi_transport_receive = int(value)

    # === MIDI Program Change ===

    @property
    def midi_program_change_send(self) -> bool:
        """Enable/disable sending program changes on pattern switch."""
        return bool(self._settings.midi_program_change_send)

    @midi_program_change_send.setter
    def midi_program_change_send(self, value: bool):
        self._settings.midi_program_change_send = int(value)

    @property
    def midi_program_change_send_ch(self) -> int:
        """MIDI channel for sending program changes (-1 = disabled, 0-15 = channel)."""
        return self._settings.midi_program_change_send_ch

    @midi_program_change_send_ch.setter
    def midi_program_change_send_ch(self, value: int):
        self._settings.midi_program_change_send_ch = value

    @property
    def midi_program_change_receive(self) -> bool:
        """Enable/disable switching patterns on incoming program change."""
        return bool(self._settings.midi_program_change_receive)

    @midi_program_change_receive.setter
    def midi_program_change_receive(self, value: bool):
        self._settings.midi_program_change_receive = int(value)

    @property
    def midi_program_change_receive_ch(self) -> int:
        """MIDI channel for receiving program changes (-1 = disabled, 0-15 = channel)."""
        return self._settings.midi_program_change_receive_ch

    @midi_program_change_receive_ch.setter
    def midi_program_change_receive_ch(self, value: int):
        self._settings.midi_program_change_receive_ch = value

    # === Recorder Settings ===

    @property
    def dynamic_recorders(self) -> bool:
        """Enable/disable dynamic recorder allocation."""
        return bool(self._settings.dynamic_recorders)

    @dynamic_recorders.setter
    def dynamic_recorders(self, value: bool):
        self._settings.dynamic_recorders = int(value)

    @property
    def record_24bit(self) -> bool:
        """Enable/disable 24-bit recording."""
        return bool(self._settings.record_24bit)

    @record_24bit.setter
    def record_24bit(self, value: bool):
        self._settings.record_24bit = int(value)

    @property
    def reserved_recorder_count(self) -> int:
        """Number of reserved recorder buffers (1-8)."""
        return self._settings.reserved_recorder_count

    @reserved_recorder_count.setter
    def reserved_recorder_count(self, value: int):
        self._settings.reserved_recorder_count = value

    @property
    def reserved_recorder_length(self) -> int:
        """Reserved recorder buffer length in bars."""
        return self._settings.reserved_recorder_length

    @reserved_recorder_length.setter
    def reserved_recorder_length(self, value: int):
        self._settings.reserved_recorder_length = value

    @property
    def load_24bit_flex(self) -> bool:
        """Enable/disable loading 24-bit samples to flex slots."""
        return bool(self._settings.load_24bit_flex)

    @load_24bit_flex.setter
    def load_24bit_flex(self, value: bool):
        self._settings.load_24bit_flex = int(value)

    # === Other Settings ===

    @property
    def write_protected(self) -> bool:
        """Get/set project write protection."""
        return bool(self._settings.write_protected)

    @write_protected.setter
    def write_protected(self, value: bool):
        self._settings.write_protected = int(value)

    @property
    def pattern_tempo_enabled(self) -> bool:
        """Enable/disable per-pattern tempo."""
        return bool(self._settings.pattern_tempo_enabled)

    @pattern_tempo_enabled.setter
    def pattern_tempo_enabled(self, value: bool):
        self._settings.pattern_tempo_enabled = int(value)

    @property
    def master_track(self) -> bool:
        """
        Enable/disable track 8 as master track.

        When enabled, track 8 receives the summed output of tracks 1-7
        and can apply effects/scenes to the entire mix.
        """
        return bool(self._settings.master_track)

    @master_track.setter
    def master_track(self, value: bool):
        self._settings.master_track = int(value)
