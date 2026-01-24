"""
Tests for ProjectFile.
"""

import pytest

from octapy._io import ProjectFile, SampleSlot


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
    """High-level Project MIDI settings tests (via project.settings)."""

    def test_midi_clock_send_default_false(self):
        """Test midi_clock_send defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_clock_send is False

    def test_midi_clock_send_set_true(self):
        """Test setting midi_clock_send to True."""
        from octapy import Project
        project = Project.from_template("TEST")
        project.settings.midi_clock_send = True
        assert project.settings.midi_clock_send is True

    def test_midi_clock_receive_default_false(self):
        """Test midi_clock_receive defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_clock_receive is False

    def test_midi_transport_send_default_false(self):
        """Test midi_transport_send defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_transport_send is False

    def test_midi_transport_receive_default_false(self):
        """Test midi_transport_receive defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_transport_receive is False

    def test_midi_program_change_send_default_false(self):
        """Test midi_program_change_send defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_program_change_send is False

    def test_midi_program_change_send_ch_default(self):
        """Test midi_program_change_send_ch defaults to -1."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_program_change_send_ch == -1

    def test_midi_program_change_receive_default_false(self):
        """Test midi_program_change_receive defaults to False."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_program_change_receive is False

    def test_midi_program_change_receive_ch_default(self):
        """Test midi_program_change_receive_ch defaults to -1."""
        from octapy import Project
        project = Project.from_template("TEST")
        assert project.settings.midi_program_change_receive_ch == -1

    @pytest.mark.slow
    def test_midi_settings_roundtrip(self, temp_dir):
        """Test that MIDI settings survive save/load via high-level API."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.midi_clock_send = True
        project.settings.midi_clock_receive = True
        project.settings.midi_transport_send = True
        project.settings.midi_transport_receive = True
        project.settings.midi_program_change_send = True
        project.settings.midi_program_change_send_ch = 10
        project.settings.midi_program_change_receive = True
        project.settings.midi_program_change_receive_ch = 5

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        # Verify
        assert loaded.settings.midi_clock_send is True
        assert loaded.settings.midi_clock_receive is True
        assert loaded.settings.midi_transport_send is True
        assert loaded.settings.midi_transport_receive is True
        assert loaded.settings.midi_program_change_send is True
        assert loaded.settings.midi_program_change_send_ch == 10
        assert loaded.settings.midi_program_change_receive is True
        assert loaded.settings.midi_program_change_receive_ch == 5


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


class TestRenderSettings:
    """Tests for octapy RenderSettings property access."""

    def test_render_settings_accessible(self):
        """Test render_settings is accessible on project."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings is not None

    def test_auto_master_trig_default_false(self):
        """Test auto_master_trig defaults to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.auto_master_trig is False

    def test_auto_master_trig_can_be_enabled(self):
        """Test auto_master_trig can be set to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.auto_master_trig = True
        assert project.render_settings.auto_master_trig is True

    def test_sample_duration_default_none(self):
        """Test sample_duration defaults to None."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.sample_duration is None

    def test_sample_duration_via_render_settings(self):
        """Test sample_duration can be set via render_settings."""
        from octapy import Project
        from octapy.api.enums import NoteLength

        project = Project.from_template("TEST")
        project.render_settings.sample_duration = NoteLength.QUARTER
        assert project.render_settings.sample_duration == NoteLength.QUARTER

    def test_sample_duration_shortcut(self):
        """Test sample_duration shortcut property on project."""
        from octapy import Project
        from octapy.api.enums import NoteLength

        project = Project.from_template("TEST")
        project.sample_duration = NoteLength.HALF
        assert project.sample_duration == NoteLength.HALF
        assert project.render_settings.sample_duration == NoteLength.HALF

    def test_auto_thru_trig_default_false(self):
        """Test auto_thru_trig defaults to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.auto_thru_trig is False

    def test_auto_thru_trig_can_be_enabled(self):
        """Test auto_thru_trig can be set to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.auto_thru_trig = True
        assert project.render_settings.auto_thru_trig is True

    def test_propagate_scenes_default_false(self):
        """Test propagate_scenes defaults to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.propagate_scenes is False

    def test_propagate_scenes_can_be_enabled(self):
        """Test propagate_scenes can be set to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.propagate_scenes = True
        assert project.render_settings.propagate_scenes is True

    def test_propagate_src_default_false(self):
        """Test propagate_src defaults to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.propagate_src is False

    def test_propagate_src_can_be_enabled(self):
        """Test propagate_src can be set to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.propagate_src = True
        assert project.render_settings.propagate_src is True

    def test_propagate_fx_default_false(self):
        """Test propagate_fx defaults to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.propagate_fx is False

    def test_transition_track_default_false(self):
        """Test transition_track defaults to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.transition_track is False

    def test_transition_track_can_be_enabled(self):
        """Test transition_track can be set to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.transition_track = True
        assert project.render_settings.transition_track is True

    def test_propagate_fx_can_be_enabled(self):
        """Test propagate_fx can be set to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.propagate_fx = True
        assert project.render_settings.propagate_fx is True


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
