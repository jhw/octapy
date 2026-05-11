"""
Settings class - project-level settings.
"""

from __future__ import annotations

from typing import List

from .._io import ProjectSettings as _ProjectSettings


class _IntFieldGroup:
    """Base helper for grouped settings views over a ProjectSettings dataclass."""

    __slots__ = ('_settings',)

    def __init__(self, project_settings: _ProjectSettings):
        object.__setattr__(self, '_settings', project_settings)


def _int_property(attr: str, doc: str = ""):
    """Build a simple int passthrough property for a ProjectSettings attribute."""
    def fget(self):
        return getattr(self._settings, attr)

    def fset(self, value):
        setattr(self._settings, attr, int(value))

    return property(fget, fset, doc=doc)


def _bool_property(attr: str, doc: str = ""):
    """Build a 0/1 int <-> bool property for a ProjectSettings attribute."""
    def fget(self):
        return bool(getattr(self._settings, attr))

    def fset(self, value):
        setattr(self._settings, attr, int(bool(value)))

    return property(fget, fset, doc=doc)


class MixerSettings(_IntFieldGroup):
    """Audio routing, gates, gains, and main/cue levels.

    These map to the Octatrack's PROJECT > MIXER and PROJECT > AUDIO menus.
    """

    input_delay_compensation = _int_property('input_delay_compensation', "PROJECT > AUDIO: input latency compensation (steps).")
    gate_ab = _int_property('gate_ab', "Input gate threshold for inputs A+B (0-127).")
    gate_cd = _int_property('gate_cd', "Input gate threshold for inputs C+D (0-127).")
    gain_ab = _int_property('gain_ab', "Input gain for inputs A+B (0-127).")
    gain_cd = _int_property('gain_cd', "Input gain for inputs C+D (0-127).")
    dir_ab = _int_property('dir_ab', "Input direct-monitor flag for A+B.")
    dir_cd = _int_property('dir_cd', "Input direct-monitor flag for C+D.")
    phones_mix = _int_property('phones_mix', "Headphone mix balance MAIN vs. CUE (0-127).")
    main_to_cue = _int_property('main_to_cue', "Route MAIN bus to the CUE bus.")
    cue_studio_mode = _int_property('cue_studio_mode', "Enable Studio Mode on the CUE bus.")
    main_level = _int_property('main_level', "MAIN output level (0-127).")
    cue_level = _int_property('cue_level', "CUE output level (0-127).")


class MetronomeSettings(_IntFieldGroup):
    """Metronome timing and volume settings.

    Maps to PROJECT > METRONOME on the Octatrack.
    """

    enabled = _bool_property('metronome_enabled', "Enable the metronome click.")
    time_signature = _int_property('metronome_time_signature', "Time signature numerator index.")
    time_signature_denominator = _int_property('metronome_time_signature_denominator', "Time signature denominator index.")
    preroll = _int_property('metronome_preroll', "Pre-roll length in bars.")
    cue_volume = _int_property('metronome_cue_volume', "Metronome volume on the CUE bus (0-127).")
    main_volume = _int_property('metronome_main_volume', "Metronome volume on the MAIN bus (0-127).")
    pitch = _int_property('metronome_pitch', "Metronome click pitch.")
    tonal = _int_property('metronome_tonal', "Use tonal click (1) instead of pure noise (0).")


class MidiPortSettings(_IntFieldGroup):
    """MIDI port routing, trig channels, and CC/note pass-through settings.

    Excludes the clock / transport / program-change flags exposed directly
    on `Settings` for backwards compatibility.
    """

    @property
    def trig_channels(self) -> List[int]:
        """Per-MIDI-track trig channel assignments (list of 8, channels 0-15)."""
        return list(self._settings.midi_trig_channels)

    @trig_channels.setter
    def trig_channels(self, value):
        value = [int(v) for v in value]
        if len(value) != 8:
            raise ValueError(f"trig_channels must have 8 entries, got {len(value)}")
        self._settings.midi_trig_channels = value

    def trig_channel(self, track_num: int) -> int:
        """Get MIDI trig channel for a track (1-8)."""
        if not 1 <= track_num <= 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        return self._settings.midi_trig_channels[track_num - 1]

    def set_trig_channel(self, track_num: int, channel: int):
        """Set MIDI trig channel for a track (1-8). Channel is 0-15."""
        if not 1 <= track_num <= 8:
            raise ValueError(f"Track number must be 1-8, got {track_num}")
        if not 0 <= channel <= 15:
            raise ValueError(f"Channel must be 0-15, got {channel}")
        self._settings.midi_trig_channels[track_num - 1] = channel

    auto_channel = _int_property('midi_auto_channel', "MIDI auto channel (used by AUTO and MIDI in).")
    soft_thru = _int_property('midi_soft_thru', "MIDI soft-thru routing.")
    audio_trk_cc_in = _int_property('midi_audio_trk_cc_in', "MIDI CC input routing for audio tracks.")
    audio_trk_cc_out = _int_property('midi_audio_trk_cc_out', "MIDI CC output routing for audio tracks.")
    audio_trk_note_in = _int_property('midi_audio_trk_note_in', "MIDI note input routing for audio tracks.")
    audio_trk_note_out = _int_property('midi_audio_trk_note_out', "MIDI note output routing for audio tracks.")
    midi_trk_cc_in = _int_property('midi_midi_trk_cc_in', "MIDI CC input routing for MIDI tracks.")

    @property
    def trig_mode_midi(self) -> List[int]:
        """Per-MIDI-track trig mode array (length 8)."""
        return list(self._settings.trig_mode_midi)

    @trig_mode_midi.setter
    def trig_mode_midi(self, value):
        value = [int(v) for v in value]
        if len(value) != 8:
            raise ValueError(f"trig_mode_midi must have 8 entries, got {len(value)}")
        self._settings.trig_mode_midi = value


class PatternChainSettings(_IntFieldGroup):
    """Behavior settings around pattern change/chain transitions.

    Maps to PROJECT > SEQUENCER on the Octatrack.
    """

    chain_behavior = _int_property('pattern_change_chain_behavior', "Pattern change chain behavior.")
    auto_silence_tracks = _bool_property('pattern_change_auto_silence_tracks', "Auto-silence tracks on pattern change.")
    auto_trig_lfos = _bool_property('pattern_change_auto_trig_lfos', "Auto-trig LFOs on pattern change.")


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
        self._mixer = MixerSettings(project_settings)
        self._metronome = MetronomeSettings(project_settings)
        self._midi = MidiPortSettings(project_settings)
        self._pattern_chain = PatternChainSettings(project_settings)

    # === Grouped sub-objects ===

    @property
    def mixer(self) -> MixerSettings:
        """Audio mixer, gates, gains, and CUE/MAIN levels."""
        return self._mixer

    @property
    def metronome(self) -> MetronomeSettings:
        """Metronome time signature, volume, pitch."""
        return self._metronome

    @property
    def midi(self) -> MidiPortSettings:
        """MIDI port settings: per-track trig channels, AUTO channel, CC/note routing."""
        return self._midi

    @property
    def pattern_chain(self) -> PatternChainSettings:
        """Pattern change/chain behavior settings."""
        return self._pattern_chain

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
        project.render_settings.recorder_track = (7, RecordingSource.MAIN)
    """

    def __init__(self):
        self._recorder_track = None
        self._recorder_slices = None

    @property
    def recorder_track(self):
        """
        Configure a track as a recorder buffer across all parts/banks.

        When set, the specified track is configured as a Flex machine playing
        its own recorder buffer, recording from the given source. This is
        applied to all parts in all banks before saving.

        Value is a tuple of (track_num, source) or None:
        - track_num: int 1-8
        - source: RecordingSource enum value

        The recorder track is automatically excluded from propagate_src and
        propagate_fx to avoid overwriting its machine configuration.

        Default is None (no automatic recorder track configuration).
        """
        return self._recorder_track

    @recorder_track.setter
    def recorder_track(self, value):
        if value is None:
            self._recorder_track = None
            return
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("recorder_track must be a (track_num, source) tuple or None")
        track_num, source = value
        if not isinstance(track_num, int) or not 1 <= track_num <= 8:
            raise ValueError(f"track_num must be 1-8, got {track_num}")
        from .enums import RecordingSource
        if not isinstance(source, RecordingSource):
            raise TypeError(f"source must be a RecordingSource, got {type(source).__name__}")
        self._recorder_track = value

    @property
    def recorder_slices(self):
        """
        Number of equal slices to pre-configure on the recorder buffer.

        When set, the recorder buffer is divided into N equal slices,
        slice mode is enabled, and trigs with STRT p-locks are placed
        at evenly-spaced positions so playback sounds identical to the
        original recording by default.

        Valid values: 2, 4, 8, 16, 32, 64, or None (disabled).
        Requires recorder_track to be set.

        Default is None (no automatic slice configuration).
        """
        return self._recorder_slices

    @recorder_slices.setter
    def recorder_slices(self, value):
        valid = {2, 4, 8, 16, 32, 64}
        if value is not None and value not in valid:
            raise ValueError(f"recorder_slices must be one of {sorted(valid)}, got {value}")
        self._recorder_slices = value

