"""
Tests for ProjectFile.
"""

from pathlib import Path

import pytest

from octapy._io import ProjectFile, SampleSlot
from octapy._io.project import read_template_file


class TestProjectFileBasics:
    """Basic ProjectFile tests."""

    def test_create_project(self, project_file):
        """Test creating a new ProjectFile."""
        assert project_file is not None

    def test_default_version(self, project_file):
        """Test default version."""
        assert project_file.version == 19

    def test_default_os_version(self, project_file):
        """Test default OS version."""
        assert "1.40" in project_file.os_version


class TestProjectFileTempo:
    """ProjectFile tempo tests."""

    def test_default_tempo(self, project_file):
        """Test default tempo is 120 BPM."""
        assert project_file.tempo == 120.0

    def test_default_tempo_x24(self, project_file):
        """Test default tempo_x24 is 2880."""
        assert project_file.tempo_x24 == 2880

    def test_set_tempo(self, project_file):
        """Test setting tempo in BPM."""
        project_file.tempo = 140.0
        assert project_file.tempo == 140.0
        assert project_file.tempo_x24 == 3360  # 140 * 24

    def test_set_tempo_x24(self, project_file):
        """Test setting raw tempo value."""
        project_file.tempo_x24 = 2400  # 100 BPM
        assert project_file.tempo == 100.0


class TestProjectFileSampleSlots:
    """ProjectFile sample slot tests."""

    def test_add_sample_slot(self, project_file):
        """Test adding a sample slot."""
        slot = project_file.add_sample_slot(
            slot_number=1,
            path="../AUDIO/sample.wav",
            slot_type="FLEX",
        )

        assert slot is not None
        assert len(project_file.sample_slots) == 1
        assert project_file.sample_slots[0].slot_number == 1
        assert project_file.sample_slots[0].path == "../AUDIO/sample.wav"

    def test_add_multiple_slots(self, project_file):
        """Test adding multiple sample slots."""
        project_file.add_sample_slot(1, "../AUDIO/kick.wav")
        project_file.add_sample_slot(2, "../AUDIO/snare.wav")
        project_file.add_sample_slot(3, "../AUDIO/hat.wav")

        assert len(project_file.sample_slots) == 3

    def test_add_recorder_slots(self, project_file):
        """Test adding recorder slots."""
        project_file.add_recorder_slots()

        # Should add 8 recorder slots (129-136)
        assert len(project_file.sample_slots) == 8

        for i, slot in enumerate(project_file.sample_slots):
            assert slot.slot_number == 129 + i

    def test_slot_properties(self, project_file):
        """Test sample slot properties."""
        slot = project_file.add_sample_slot(
            slot_number=1,
            path="../AUDIO/sample.wav",
            slot_type="FLEX",
            gain=64,
            loop_mode=1,
            timestretch_mode=2,
        )

        assert slot.slot_type == "FLEX"
        assert slot.gain == 64
        assert slot.loop_mode == 1
        assert slot.timestretch_mode == 2


class TestProjectFileRoundTrip:
    """ProjectFile read/write round-trip tests."""

    def test_write_read_roundtrip(self, project_file, temp_dir):
        """Test that write then read preserves data."""
        path = temp_dir / "project.work"

        # Add some data
        project_file.tempo = 130.0
        project_file.add_sample_slot(1, "../AUDIO/kick.wav", slot_type="FLEX")
        project_file.add_sample_slot(2, "../AUDIO/snare.wav", slot_type="FLEX")

        # Write
        project_file.to_file(path)

        # Read back
        loaded = ProjectFile.from_file(path)

        # Verify
        assert loaded.tempo == 130.0
        assert len(loaded.sample_slots) == 2
        assert loaded.sample_slots[0].slot_number == 1
        assert loaded.sample_slots[1].slot_number == 2

    def test_tempo_survives_roundtrip(self, project_file, temp_dir):
        """Test that tempo survives save/load."""
        path = temp_dir / "project.work"

        project_file.tempo = 124.0
        project_file.to_file(path)

        loaded = ProjectFile.from_file(path)
        assert loaded.tempo == 124.0
        assert loaded.tempo_x24 == 2976  # 124 * 24

    def test_crlf_line_endings(self, project_file, temp_dir):
        """Test that output uses CRLF line endings."""
        path = temp_dir / "project.work"
        project_file.to_file(path)

        with open(path, 'rb') as f:
            content = f.read()

        # Should contain CRLF
        assert b'\r\n' in content

        # Should not contain lone LF (except after CR)
        lines = content.split(b'\r\n')
        for line in lines[:-1]:  # Exclude last which may be empty
            assert b'\n' not in line


class TestProjectFileMidiSettings:
    """ProjectFile MIDI settings tests."""

    def test_default_midi_clock_send(self, project_file):
        """Test default MIDI clock send is disabled."""
        assert project_file.settings.midi_clock_send == 0

    def test_default_midi_clock_receive(self, project_file):
        """Test default MIDI clock receive is disabled."""
        assert project_file.settings.midi_clock_receive == 0

    def test_default_midi_transport_send(self, project_file):
        """Test default MIDI transport send is disabled."""
        assert project_file.settings.midi_transport_send == 0

    def test_default_midi_transport_receive(self, project_file):
        """Test default MIDI transport receive is disabled."""
        assert project_file.settings.midi_transport_receive == 0

    def test_default_midi_program_change_send(self, project_file):
        """Test default MIDI program change send is disabled."""
        assert project_file.settings.midi_program_change_send == 0

    def test_default_midi_program_change_send_ch(self, project_file):
        """Test default MIDI program change send channel is -1."""
        assert project_file.settings.midi_program_change_send_ch == -1

    def test_default_midi_program_change_receive(self, project_file):
        """Test default MIDI program change receive is disabled."""
        assert project_file.settings.midi_program_change_receive == 0

    def test_default_midi_program_change_receive_ch(self, project_file):
        """Test default MIDI program change receive channel is -1."""
        assert project_file.settings.midi_program_change_receive_ch == -1

    def test_midi_settings_roundtrip(self, project_file, temp_dir):
        """Test MIDI settings survive save/load."""
        path = temp_dir / "project.work"

        # Set all MIDI settings
        project_file.settings.midi_clock_send = 1
        project_file.settings.midi_clock_receive = 1
        project_file.settings.midi_transport_send = 1
        project_file.settings.midi_transport_receive = 1
        project_file.settings.midi_program_change_send = 1
        project_file.settings.midi_program_change_send_ch = 10
        project_file.settings.midi_program_change_receive = 1
        project_file.settings.midi_program_change_receive_ch = 5

        # Write
        project_file.to_file(path)

        # Read back
        loaded = ProjectFile.from_file(path)

        # Verify
        assert loaded.settings.midi_clock_send == 1
        assert loaded.settings.midi_clock_receive == 1
        assert loaded.settings.midi_transport_send == 1
        assert loaded.settings.midi_transport_receive == 1
        assert loaded.settings.midi_program_change_send == 1
        assert loaded.settings.midi_program_change_send_ch == 10
        assert loaded.settings.midi_program_change_receive == 1
        assert loaded.settings.midi_program_change_receive_ch == 5


class TestProjectSettingsFullCoverage:
    """Round-trip coverage for every ProjectSettings field.

    Phase 1.1: prior to this, many INI fields were hardcoded by the writer,
    so non-default values silently snapped back to template defaults on save.
    """

    def test_template_roundtrip_byte_identical(self, temp_dir):
        """Writing a fresh ProjectFile reproduces the embedded template byte-for-byte."""
        original = read_template_file("project.work")

        project = ProjectFile.new()
        path = temp_dir / "project.work"
        project.to_file(path)
        written = path.read_bytes()

        assert written == original

    def test_all_settings_fields_preserved(self, temp_dir):
        """Every settings field round-trips with a non-default value."""
        project = ProjectFile.new()
        s = project.settings

        # Apply non-default values to every field
        s.write_protected = 1
        s.tempo_x24 = 3000
        s.pattern_tempo_enabled = 1
        s.midi_clock_send = 1
        s.midi_clock_receive = 1
        s.midi_transport_send = 1
        s.midi_transport_receive = 1
        s.midi_program_change_send = 1
        s.midi_program_change_send_ch = 7
        s.midi_program_change_receive = 1
        s.midi_program_change_receive_ch = 8
        s.midi_trig_channels = [9, 10, 11, 12, 13, 14, 15, 0]
        s.midi_auto_channel = 5
        s.midi_soft_thru = 1
        s.midi_audio_trk_cc_in = 0
        s.midi_audio_trk_cc_out = 2
        s.midi_audio_trk_note_in = 0
        s.midi_audio_trk_note_out = 2
        s.midi_midi_trk_cc_in = 0
        s.pattern_change_chain_behavior = 1
        s.pattern_change_auto_silence_tracks = 1
        s.pattern_change_auto_trig_lfos = 1
        s.load_24bit_flex = 1
        s.dynamic_recorders = 1
        s.record_24bit = 1
        s.reserved_recorder_count = 4
        s.reserved_recorder_length = 32
        s.input_delay_compensation = 5
        s.gate_ab = 100
        s.gate_cd = 80
        s.gain_ab = 50
        s.gain_cd = 70
        s.dir_ab = 1
        s.dir_cd = 1
        s.phones_mix = 90
        s.main_to_cue = 1
        s.master_track = 1
        s.cue_studio_mode = 1
        s.main_level = 100
        s.cue_level = 110
        s.metronome_time_signature = 4
        s.metronome_time_signature_denominator = 1
        s.metronome_preroll = 2
        s.metronome_cue_volume = 64
        s.metronome_main_volume = 32
        s.metronome_pitch = 24
        s.metronome_tonal = 0
        s.metronome_enabled = 1
        s.trig_mode_midi = [1, 2, 3, 4, 5, 6, 7, 0]

        path = temp_dir / "project.work"
        project.to_file(path)
        loaded = ProjectFile.from_file(path)

        for attr in vars(s):
            assert getattr(loaded.settings, attr) == getattr(s, attr), (
                f"Settings.{attr} not preserved: wrote {getattr(s, attr)!r} got {getattr(loaded.settings, attr)!r}"
            )

    def test_state_fields_preserved(self, temp_dir):
        """Every ProjectState field round-trips with non-default values."""
        project = ProjectFile.new()
        st = project.state

        st.bank = 3
        st.pattern = 7
        st.arrangement = 1
        st.arrangement_mode = 1
        st.part = 2
        st.track = 4
        st.track_othermode = 1
        st.scene_a_mute = 1
        st.scene_b_mute = 1
        st.track_cue_mask = 0xAB
        st.track_mute_mask = 0xCD
        st.track_solo_mask = 0xEF
        st.midi_track_mute_mask = 0x12
        st.midi_track_solo_mask = 0x34
        st.midi_mode = 1

        path = temp_dir / "project.work"
        project.to_file(path)
        loaded = ProjectFile.from_file(path)

        for attr in vars(st):
            assert getattr(loaded.state, attr) == getattr(st, attr), (
                f"State.{attr} not preserved: wrote {getattr(st, attr)!r} got {getattr(loaded.state, attr)!r}"
            )

    def test_midi_trig_channels_default(self, project_file):
        """Default MIDI_TRIG_CHn values are 0..7."""
        assert project_file.settings.midi_trig_channels == [0, 1, 2, 3, 4, 5, 6, 7]

    def test_midi_trig_channels_roundtrip(self, project_file, temp_dir):
        """Per-track MIDI trig channels survive a round-trip."""
        project_file.settings.midi_trig_channels = [15, 14, 13, 12, 11, 10, 9, 8]
        path = temp_dir / "project.work"
        project_file.to_file(path)

        loaded = ProjectFile.from_file(path)
        assert loaded.settings.midi_trig_channels == [15, 14, 13, 12, 11, 10, 9, 8]

    def test_trig_mode_midi_default(self, project_file):
        """Default TRIG_MODE_MIDI array is all zeros."""
        assert project_file.settings.trig_mode_midi == [0] * 8

    def test_trig_mode_midi_roundtrip(self, project_file, temp_dir):
        """Per-track trig_mode_midi values survive a round-trip."""
        project_file.settings.trig_mode_midi = [3, 2, 1, 0, 1, 2, 3, 0]
        path = temp_dir / "project.work"
        project_file.to_file(path)

        loaded = ProjectFile.from_file(path)
        assert loaded.settings.trig_mode_midi == [3, 2, 1, 0, 1, 2, 3, 0]

    def test_metronome_defaults_match_template(self, project_file):
        """Metronome defaults match the OT template."""
        s = project_file.settings
        assert s.metronome_time_signature == 3
        assert s.metronome_time_signature_denominator == 2
        assert s.metronome_preroll == 0
        assert s.metronome_cue_volume == 32
        assert s.metronome_main_volume == 0
        assert s.metronome_pitch == 12
        assert s.metronome_tonal == 1
        assert s.metronome_enabled == 0

    def test_mixer_defaults_match_template(self, project_file):
        """Mixer/input defaults match the OT template."""
        s = project_file.settings
        assert s.gate_ab == 127
        assert s.gate_cd == 127
        assert s.gain_ab == 64
        assert s.gain_cd == 64
        assert s.phones_mix == 64
        assert s.main_level == 64
        assert s.cue_level == 64

    def test_ot_tools_io_blank_project_roundtrip(self, temp_dir):
        """ot-tools-io's blank-project/project.work round-trips byte-identical."""
        src = Path("/Users/jhw/work/ot-tools-io/ot-tools-io/test-data/blank-project/project.work")
        if not src.exists():
            pytest.skip("ot-tools-io test data not present")
        original = src.read_bytes()

        project = ProjectFile.from_file(src)
        path = temp_dir / "project.work"
        project.to_file(path)

        assert path.read_bytes() == original


class TestSampleSlot:
    """SampleSlot tests."""

    def test_default_values(self):
        """Test SampleSlot default values."""
        slot = SampleSlot()

        assert slot.slot_type == "FLEX"
        assert slot.slot_number == 1
        assert slot.path == ""
        assert slot.bpm_x24 == 2880
        assert slot.gain == 48

    def test_to_ini_block(self):
        """Test INI block generation."""
        slot = SampleSlot(
            slot_type="FLEX",
            slot_number=1,
            path="../AUDIO/kick.wav",
            gain=48,
        )

        ini = slot.to_ini_block()

        assert "[SAMPLE]" in ini
        assert "TYPE=FLEX" in ini
        assert "SLOT=001" in ini
        assert "PATH=../AUDIO/kick.wav" in ini
        assert "[/SAMPLE]" in ini


class TestProjectMidiSettings:
    """High-level project MIDI settings via project.settings.midi."""

    def test_midi_clock_send_default_false(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.clock_send is False

    def test_midi_clock_send_set_true(self):
        from octapy import Project
        project = Project.from_template("TEST")
        project.settings.midi.clock_send = True
        assert project.settings.midi.clock_send is True

    def test_midi_clock_receive_default_false(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.clock_receive is False

    def test_midi_transport_send_default_false(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.transport_send is False

    def test_midi_transport_receive_default_false(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.transport_receive is False

    def test_midi_program_change_send_default_false(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.program_change_send is False

    def test_midi_program_change_send_ch_default(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.program_change_send_ch == -1

    def test_midi_program_change_receive_default_false(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.program_change_receive is False

    def test_midi_program_change_receive_ch_default(self):
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi.program_change_receive_ch == -1

    @pytest.mark.slow
    def test_midi_settings_roundtrip(self, temp_dir):
        """MIDI settings survive save/load via the grouped API."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.midi.clock_send = True
        project.settings.midi.clock_receive = True
        project.settings.midi.transport_send = True
        project.settings.midi.transport_receive = True
        project.settings.midi.program_change_send = True
        project.settings.midi.program_change_send_ch = 10
        project.settings.midi.program_change_receive = True
        project.settings.midi.program_change_receive_ch = 5

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        assert loaded.settings.midi.clock_send is True
        assert loaded.settings.midi.clock_receive is True
        assert loaded.settings.midi.transport_send is True
        assert loaded.settings.midi.transport_receive is True
        assert loaded.settings.midi.program_change_send is True
        assert loaded.settings.midi.program_change_send_ch == 10
        assert loaded.settings.midi.program_change_receive is True
        assert loaded.settings.midi.program_change_receive_ch == 5


class TestMasterTrackSettings:
    """Master track settings tests."""

    def test_master_track_default_false(self):
        """Test master_track defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.master_track is False

    def test_master_track_set_true(self):
        """Test setting master_track to True."""
        from octapy import Project
        project = Project.from_template("TEST")
        project.settings.master_track = True
        assert project.settings.master_track is True

    @pytest.mark.slow
    def test_master_track_roundtrip(self, temp_dir):
        """Test that master_track setting survives save/load."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        # Verify
        assert loaded.settings.master_track is True


class TestConfigureRecorderBuffer:
    """Tests for Project.configure_recorder_buffer() — eager replacement
    for the old render_settings.recorder_track / recorder_slices pair."""

    def _project(self):
        from octapy import Project
        return Project.from_template("TEST")

    def test_eager_configures_all_64_part_tracks(self):
        """One call configures the named track across every bank/part."""
        from octapy import RecordingSource
        from octapy.api.enums import MachineType

        project = self._project()
        project.configure_recorder_buffer(7, RecordingSource.MAIN)

        for bank_num in range(1, 17):
            for part_num in range(1, 5):
                track = project.bank(bank_num).part(part_num).track(7)
                assert track.machine_type == MachineType.FLEX
                assert track.recorder.source == RecordingSource.MAIN

    def test_immediately_visible_in_project_state(self):
        """Post-call inspection shows the configured state — no save needed."""
        from octapy import RecordingSource

        project = self._project()
        # Default recorder.source is OFF (octapy baseline)
        assert project.bank(1).part(1).track(7).recorder.source == RecordingSource.OFF

        project.configure_recorder_buffer(7, RecordingSource.MAIN)
        assert project.bank(1).part(1).track(7).recorder.source == RecordingSource.MAIN

    def test_track_8_rejected_when_master_track_enabled(self):
        """Validation happens at the call site, not at save time."""
        from octapy import RecordingSource

        project = self._project()
        project.settings.master_track = True
        with pytest.raises(ValueError, match="track 8.*master_track"):
            project.configure_recorder_buffer(8, RecordingSource.MAIN)

    def test_invalid_track_rejected(self):
        from octapy import RecordingSource

        project = self._project()
        with pytest.raises(ValueError):
            project.configure_recorder_buffer(0, RecordingSource.MAIN)
        with pytest.raises(ValueError):
            project.configure_recorder_buffer(9, RecordingSource.MAIN)

    def test_invalid_source_type_rejected(self):
        project = self._project()
        with pytest.raises(TypeError):
            project.configure_recorder_buffer(7, "MAIN")  # not an enum value


class TestSettingsGroups:
    """Tests for grouped settings (mixer, metronome, midi, pattern_chain)."""

    def _project(self):
        from octapy import Project
        return Project.from_template("TEST")

    def test_mixer_defaults_visible(self):
        p = self._project()
        assert p.settings.mixer.main_level == 64
        assert p.settings.mixer.cue_level == 64
        assert p.settings.mixer.gate_ab == 127
        assert p.settings.mixer.phones_mix == 64

    def test_mixer_setters(self):
        p = self._project()
        p.settings.mixer.main_level = 100
        p.settings.mixer.cue_level = 110
        p.settings.mixer.phones_mix = 90
        assert p.settings.mixer.main_level == 100
        assert p.settings.mixer.cue_level == 110
        assert p.settings.mixer.phones_mix == 90
        # Backing dataclass also updated
        assert p._project_file.settings.main_level == 100

    def test_metronome_defaults(self):
        p = self._project()
        assert p.settings.metronome.enabled is False
        assert p.settings.metronome.time_signature == 3
        assert p.settings.metronome.cue_volume == 32
        assert p.settings.metronome.pitch == 12

    def test_metronome_setters(self):
        p = self._project()
        p.settings.metronome.enabled = True
        p.settings.metronome.cue_volume = 64
        p.settings.metronome.pitch = 24
        assert p.settings.metronome.enabled is True
        assert p.settings.metronome.cue_volume == 64
        assert p.settings.metronome.pitch == 24

    def test_midi_defaults(self):
        p = self._project()
        assert p.settings.midi.trig_channels == [0, 1, 2, 3, 4, 5, 6, 7]
        assert p.settings.midi.auto_channel == 10
        assert p.settings.midi.soft_thru == 0

    def test_midi_set_trig_channel(self):
        p = self._project()
        p.settings.midi.set_trig_channel(1, 9)
        p.settings.midi.set_trig_channel(8, 0)
        assert p.settings.midi.trig_channel(1) == 9
        assert p.settings.midi.trig_channel(8) == 0
        # Others untouched
        assert p.settings.midi.trig_channel(2) == 1

    def test_midi_set_trig_channel_validation(self):
        p = self._project()
        with pytest.raises(ValueError):
            p.settings.midi.set_trig_channel(0, 5)
        with pytest.raises(ValueError):
            p.settings.midi.set_trig_channel(9, 5)
        with pytest.raises(ValueError):
            p.settings.midi.set_trig_channel(1, 16)

    def test_midi_trig_channels_setter_validates_length(self):
        p = self._project()
        with pytest.raises(ValueError):
            p.settings.midi.trig_channels = [0, 1, 2]  # too few

    def test_midi_trig_mode_midi(self):
        p = self._project()
        assert p.settings.midi.trig_mode_midi == [0] * 8
        p.settings.midi.trig_mode_midi = [1, 2, 3, 4, 5, 6, 7, 0]
        assert p.settings.midi.trig_mode_midi == [1, 2, 3, 4, 5, 6, 7, 0]

    def test_pattern_chain_defaults(self):
        p = self._project()
        assert p.settings.pattern_chain.chain_behavior == 0
        assert p.settings.pattern_chain.auto_silence_tracks is False
        assert p.settings.pattern_chain.auto_trig_lfos is False

    def test_pattern_chain_setters(self):
        p = self._project()
        p.settings.pattern_chain.chain_behavior = 1
        p.settings.pattern_chain.auto_silence_tracks = True
        p.settings.pattern_chain.auto_trig_lfos = True
        assert p.settings.pattern_chain.chain_behavior == 1
        assert p.settings.pattern_chain.auto_silence_tracks is True
        assert p.settings.pattern_chain.auto_trig_lfos is True

    def test_memory_defaults(self):
        p = self._project()
        assert p.settings.memory.load_24bit_flex is False
        assert p.settings.memory.dynamic_recorders is False
        assert p.settings.memory.record_24bit is False
        assert p.settings.memory.reserved_recorder_count == 8
        assert p.settings.memory.reserved_recorder_length == 16

    def test_memory_setters(self):
        p = self._project()
        p.settings.memory.record_24bit = True
        p.settings.memory.dynamic_recorders = True
        p.settings.memory.reserved_recorder_count = 4
        p.settings.memory.reserved_recorder_length = 32
        assert p.settings.memory.record_24bit is True
        assert p.settings.memory.dynamic_recorders is True
        assert p.settings.memory.reserved_recorder_count == 4
        assert p.settings.memory.reserved_recorder_length == 32

    def test_grouped_settings_round_trip_via_project_file(self, temp_dir):
        """Mutations through the grouped API survive ProjectFile.to_file roundtrip."""
        from octapy import Project

        p = Project.from_template("TEST")
        p.settings.mixer.main_level = 100
        p.settings.metronome.enabled = True
        p.settings.metronome.cue_volume = 64
        p.settings.midi.set_trig_channel(1, 9)
        p.settings.midi.auto_channel = 5
        p.settings.pattern_chain.auto_trig_lfos = True

        path = temp_dir / "project.work"
        p._project_file.to_file(path)

        loaded_pf = type(p._project_file).from_file(path)
        from octapy.api.settings import Settings
        loaded = Settings(loaded_pf.settings)

        assert loaded.mixer.main_level == 100
        assert loaded.metronome.enabled is True
        assert loaded.metronome.cue_volume == 64
        assert loaded.midi.trig_channel(1) == 9
        assert loaded.midi.auto_channel == 5
        assert loaded.pattern_chain.auto_trig_lfos is True


class TestSceneIsBlank:
    """Tests for Scene.is_blank property."""

    def test_new_scene_is_blank(self):
        """A fresh scene should be blank."""
        from octapy import Project

        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        assert scene.is_blank is True

    def test_scene_with_lock_is_not_blank(self):
        """A scene with any lock should not be blank."""
        from octapy import Project

        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        scene.track(1).amp_volume = 100
        assert scene.is_blank is False

    def test_scene_after_clear_is_blank(self):
        """A scene after clear_all_locks should be blank."""
        from octapy import Project

        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        scene.track(1).amp_volume = 100
        scene.clear_all_locks()
        assert scene.is_blank is True


class TestSampleCopy:
    """Tests for sample copying during project save."""

    @pytest.mark.slow
    def test_project_copies_samples_unchanged(self, tmp_path):
        """Project copies samples as-is when saving."""
        from octapy import Project
        from pydub import AudioSegment

        # Create a test sample (500ms)
        samples_dir = tmp_path / "samples"
        samples_dir.mkdir()
        source = AudioSegment.silent(duration=500)
        sample_path = samples_dir / "test.wav"
        source.export(str(sample_path), format="wav")

        project = Project.from_template("TEST")
        project.add_sample(sample_path)

        output_dir = tmp_path / "output"
        project.to_directory(output_dir)

        result_path = output_dir / "samples" / "test.wav"
        result = AudioSegment.from_wav(str(result_path))
        assert len(result) == 500


class TestRecorderSlices:
    """Tests for the slices=N kwarg on configure_recorder_buffer().

    Workflow: set pattern activity FIRST, then call configure_recorder_buffer
    last — slice-trig placement is activity-dependent and runs eagerly.
    """

    def test_slices_valid_values_that_divide_rlen(self):
        """Valid slice counts that divide the octapy-default RLEN=16 apply cleanly."""
        from octapy import Project, RecordingSource

        # Octapy default RLEN is 16. Slice values 2, 4, 8, 16 divide it evenly.
        for value in [2, 4, 8, 16]:
            project = Project.from_template("TEST")
            project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=value)

    def test_slices_must_divide_rlen(self):
        """slices=32 or 64 raises ValueError when RLEN=16 (octapy default)."""
        from octapy import Project, RecordingSource

        project = Project.from_template("TEST")
        with pytest.raises(ValueError, match="does not divide evenly"):
            project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=32)

    def test_slices_invalid_value(self):
        """Non-power-of-two slice counts (and similar) are rejected."""
        from octapy import Project, RecordingSource

        for value in [3, 5, 6, 7, 10, 128]:
            project = Project.from_template("TEST")
            with pytest.raises(ValueError, match="slices must be one of"):
                project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=value)

    @pytest.mark.slow
    def test_slices_enables_slice_mode_on_all_parts(self, temp_dir):
        """slices=N turns on slice mode for the recorder track across all parts."""
        from octapy import Project, RecordingSource

        project = Project.from_template("TEST")
        project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]
        project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)

        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        for part_num in range(1, 5):
            track = loaded.bank(1).part(part_num).track(7)
            assert track.setup.slice == 1

    def test_slices_places_trigs(self):
        """4 slices with RLEN=16 places trigs at 1, 5, 9, 13 in patterns with activity."""
        from octapy import Project, RecordingSource

        project = Project.from_template("TEST")
        project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]
        project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)

        rec_track = project.bank(1).pattern(1).audio_track(7)
        assert rec_track.active_steps == [1, 5, 9, 13]

    def test_slices_sets_strt_plocks(self):
        """4 slices sets slice_index p-locks to 0, 1, 2, 3."""
        from octapy import Project, RecordingSource

        project = Project.from_template("TEST")
        project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]
        project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)

        rec_track = project.bank(1).pattern(1).audio_track(7)
        for i, step_num in enumerate([1, 5, 9, 13]):
            assert rec_track.step(step_num).slice_index == i

    def test_slices_no_trigs_in_empty_patterns(self):
        """Patterns with no activity get no recorder-track trigs."""
        from octapy import Project, RecordingSource

        project = Project.from_template("TEST")
        # No activity added.
        project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)

        for pattern_num in range(1, 17):
            rec_track = project.bank(1).pattern(pattern_num).audio_track(7)
            assert rec_track.active_steps == []

    def test_slices_8_trig_positions(self):
        """8 slices with RLEN=16 places trigs at 1, 3, 5, 7, 9, 11, 13, 15."""
        from octapy import Project, RecordingSource

        project = Project.from_template("TEST")
        project.bank(1).pattern(1).audio_track(1).active_steps = [1]
        project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=8)

        rec_track = project.bank(1).pattern(1).audio_track(7)
        assert rec_track.active_steps == [1, 3, 5, 7, 9, 11, 13, 15]
        for i, step_num in enumerate([1, 3, 5, 7, 9, 11, 13, 15]):
            assert rec_track.step(step_num).slice_index == i
