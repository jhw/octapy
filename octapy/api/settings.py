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


class RenderSettings:
    """
    Octapy-specific settings used during project rendering/saving.

    These settings are NOT saved to Octatrack files - they control
    octapy's behavior when processing and saving projects.

    Access via project.render_settings.

    Usage:
        project.render_settings.auto_master_trig = True
        project.render_settings.auto_thru_trig = True
        project.render_settings.propagate_scenes = True
        project.render_settings.sample_duration = NoteLength.QUARTER
    """

    def __init__(self):
        self._auto_master_trig = False
        self._auto_thru_trig = False
        self._propagate_scenes = False
        self._propagate_amp = False
        self._propagate_fx = False
        self._sample_duration = None

    @property
    def auto_master_trig(self) -> bool:
        """
        Auto-add trig to track 8 when master track is enabled.

        When True, automatically adds a step 1 trig to track 8 for any
        pattern where tracks 1-7 have trigs. This ensures the master
        track processes audio.

        Default is False (manual control over track 8 trigs).
        """
        return self._auto_master_trig

    @auto_master_trig.setter
    def auto_master_trig(self, value: bool):
        self._auto_master_trig = value

    @property
    def auto_thru_trig(self) -> bool:
        """
        Auto-add trig to tracks with Thru machines.

        When True, automatically adds a step 1 trig to any track with a
        Thru machine in patterns that have audio activity. Thru machines
        need a trig to process incoming external audio.

        Default is False (manual control over Thru track trigs).
        """
        return self._auto_thru_trig

    @auto_thru_trig.setter
    def auto_thru_trig(self, value: bool):
        self._auto_thru_trig = value

    @property
    def propagate_scenes(self) -> bool:
        """
        Propagate scenes from Part 1 to Parts 2-4 within each bank.

        When True, any scene with locks defined in Part 1 is automatically
        copied to the same scene number in Parts 2, 3, and 4. This ensures
        consistent scene behavior when switching Parts.

        Default is False (manual scene configuration per Part).
        """
        return self._propagate_scenes

    @propagate_scenes.setter
    def propagate_scenes(self, value: bool):
        self._propagate_scenes = value

    @property
    def propagate_amp(self) -> bool:
        """
        Propagate AMP page settings from Part 1 to Parts 2-4 within each bank.

        When True, copies AMP settings (attack, hold, release, volume, balance)
        from Part 1 to Parts 2-4 for each track, but only if the target Part's
        AMP page is at template defaults.

        Default is False (manual AMP configuration per Part).
        """
        return self._propagate_amp

    @propagate_amp.setter
    def propagate_amp(self, value: bool):
        self._propagate_amp = value

    @property
    def propagate_fx(self) -> bool:
        """
        Propagate FX1 and FX2 page settings from Part 1 to Parts 2-4 within each bank.

        When True, copies FX type and parameters from Part 1 to Parts 2-4
        for each track, but only if the target Part's FX type matches the
        template defaults (FX1=FILTER, FX2=DELAY).

        Default is False (manual FX configuration per Part).
        """
        return self._propagate_fx

    @propagate_fx.setter
    def propagate_fx(self, value: bool):
        self._propagate_fx = value

    @property
    def sample_duration(self):
        """
        Target duration for sample normalization.

        When set, samples are normalized (trimmed/padded) to this duration
        based on project BPM when saving.

        Values: NoteLength.SIXTEENTH (1 step), EIGHTH (2 steps),
                QUARTER (4 steps), HALF (8 steps), WHOLE (16 steps),
                or None (no normalization, default)
        """
        return self._sample_duration

    @sample_duration.setter
    def sample_duration(self, value):
        self._sample_duration = value
