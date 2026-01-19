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

    @pytest.mark.slow
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

    @pytest.mark.slow
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

    @pytest.mark.slow
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


class TestMasterTrackAutoTrig:
    """Tests for auto-trig logic when master track is enabled."""

    @pytest.mark.slow
    def test_auto_trig_not_added_when_master_disabled(self, temp_dir):
        """Track 8 should NOT get auto-trig when master_track is disabled."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = False
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 8 should remain empty
        assert project.bank(1).pattern(1).track(8).active_steps == []

    @pytest.mark.slow
    def test_auto_trig_added_when_master_enabled(self, temp_dir):
        """Track 8 should get step 1 trig when master_track is enabled."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 8 should have step 1
        assert 1 in project.bank(1).pattern(1).track(8).active_steps

    @pytest.mark.slow
    def test_auto_trig_preserves_existing_track8_steps(self, temp_dir):
        """Auto-trig should preserve existing steps on track 8."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]
        project.bank(1).pattern(1).track(8).active_steps = [5, 9]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 8 should have step 1 plus original steps
        active = project.bank(1).pattern(1).track(8).active_steps
        assert 1 in active
        assert 5 in active
        assert 9 in active

    @pytest.mark.slow
    def test_auto_trig_no_duplicate_if_step1_exists(self, temp_dir):
        """Auto-trig should not duplicate step 1 if already present."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]
        project.bank(1).pattern(1).track(8).active_steps = [1, 5, 9]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 8 should still have exactly [1, 5, 9]
        active = project.bank(1).pattern(1).track(8).active_steps
        assert active.count(1) == 1  # No duplicates

    @pytest.mark.slow
    def test_auto_trig_skips_pattern_with_no_trigs(self, temp_dir):
        """Patterns with no trigs on tracks 1-7 should not get auto-trig."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True
        # Pattern 1 has no trigs on tracks 1-7

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 8 should remain empty
        assert project.bank(1).pattern(1).track(8).active_steps == []

    @pytest.mark.slow
    def test_auto_trig_only_audio_tracks_matter(self, temp_dir):
        """Only audio tracks 1-7 should trigger auto-trig, not MIDI."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True
        # Only set trigs on MIDI track, not audio
        project.bank(1).pattern(1).midi_track(1).active_steps = [1, 5, 9, 13]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 8 should remain empty (MIDI trigs don't count)
        assert project.bank(1).pattern(1).track(8).active_steps == []

    @pytest.mark.slow
    def test_auto_trig_across_multiple_banks(self, temp_dir):
        """Auto-trig should work across all banks."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True

        # Set trigs in banks 1 and 3
        project.bank(1).pattern(1).track(1).active_steps = [1, 5]
        project.bank(3).pattern(5).track(2).active_steps = [1, 9]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Both patterns should have track 8 step 1
        assert 1 in project.bank(1).pattern(1).track(8).active_steps
        assert 1 in project.bank(3).pattern(5).track(8).active_steps

        # Pattern with no trigs should remain empty
        assert project.bank(2).pattern(1).track(8).active_steps == []


class TestRenderSettings:
    """Tests for octapy RenderSettings."""

    def test_render_settings_accessible(self):
        """Test render_settings is accessible on project."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings is not None

    def test_auto_master_trig_default_true(self):
        """Test auto_master_trig defaults to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.auto_master_trig is True

    def test_auto_master_trig_can_be_disabled(self):
        """Test auto_master_trig can be set to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.auto_master_trig = False
        assert project.render_settings.auto_master_trig is False

    @pytest.mark.slow
    def test_auto_master_trig_disabled_prevents_auto_trig(self, temp_dir):
        """When auto_master_trig is False, track 8 trigs are not auto-added."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.settings.master_track = True
        project.render_settings.auto_master_trig = False
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]

        # Save - should NOT add auto-trig because disabled
        project.to_directory(temp_dir / "TEST")

        # Track 8 should remain empty
        assert project.bank(1).pattern(1).track(8).active_steps == []

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

    def test_auto_thru_trig_default_true(self):
        """Test auto_thru_trig defaults to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.auto_thru_trig is True

    def test_auto_thru_trig_can_be_disabled(self):
        """Test auto_thru_trig can be set to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.auto_thru_trig = False
        assert project.render_settings.auto_thru_trig is False

    def test_propagate_scenes_default_true(self):
        """Test propagate_scenes defaults to True."""
        from octapy import Project

        project = Project.from_template("TEST")
        assert project.render_settings.propagate_scenes is True

    def test_propagate_scenes_can_be_disabled(self):
        """Test propagate_scenes can be set to False."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.propagate_scenes = False
        assert project.render_settings.propagate_scenes is False


class TestAutoThruTrig:
    """Tests for auto-trig logic for Thru machines."""

    @pytest.mark.slow
    def test_auto_thru_trig_adds_step1(self, temp_dir):
        """Thru track should get step 1 trig when pattern has activity."""
        from octapy import Project, MachineType

        project = Project.from_template("TEST")
        # Set track 2 to Thru machine
        project.bank(1).part(1).track(2).machine_type = MachineType.THRU
        # Add trigs to track 1
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]

        # Save triggers the auto-trig logic
        project.to_directory(temp_dir / "TEST")

        # Track 2 (Thru) should have step 1
        assert 1 in project.bank(1).pattern(1).track(2).active_steps

    @pytest.mark.slow
    def test_auto_thru_trig_disabled_prevents_auto_trig(self, temp_dir):
        """When auto_thru_trig is False, Thru tracks don't get auto-trigs."""
        from octapy import Project, MachineType

        project = Project.from_template("TEST")
        project.render_settings.auto_thru_trig = False
        # Set track 2 to Thru machine
        project.bank(1).part(1).track(2).machine_type = MachineType.THRU
        # Add trigs to track 1
        project.bank(1).pattern(1).track(1).active_steps = [1, 5, 9, 13]

        # Save
        project.to_directory(temp_dir / "TEST")

        # Track 2 should remain empty
        assert project.bank(1).pattern(1).track(2).active_steps == []

    @pytest.mark.slow
    def test_auto_thru_trig_skips_empty_patterns(self, temp_dir):
        """Patterns with no activity should not get Thru auto-trigs."""
        from octapy import Project, MachineType

        project = Project.from_template("TEST")
        # Set track 2 to Thru machine but no trigs anywhere
        project.bank(1).part(1).track(2).machine_type = MachineType.THRU

        # Save
        project.to_directory(temp_dir / "TEST")

        # Track 2 should remain empty
        assert project.bank(1).pattern(1).track(2).active_steps == []


class TestPropagateScenes:
    """Tests for scene propagation from Part 1 to Parts 2-4."""

    @pytest.mark.slow
    def test_scene_propagates_to_other_parts(self, temp_dir):
        """Scene with locks in Part 1 should copy to Parts 2-4."""
        from octapy import Project

        project = Project.from_template("TEST")
        # Set a scene lock in Part 1
        project.bank(1).part(1).scene(3).track(1).amp_volume = 100

        # Save triggers the propagation
        project.to_directory(temp_dir / "TEST")

        # Scene 3 should be copied to Parts 2, 3, 4
        assert project.bank(1).part(2).scene(3).track(1).amp_volume == 100
        assert project.bank(1).part(3).scene(3).track(1).amp_volume == 100
        assert project.bank(1).part(4).scene(3).track(1).amp_volume == 100

    @pytest.mark.slow
    def test_scene_propagation_disabled(self, temp_dir):
        """When propagate_scenes is False, scenes don't copy."""
        from octapy import Project

        project = Project.from_template("TEST")
        project.render_settings.propagate_scenes = False
        # Set a scene lock in Part 1
        project.bank(1).part(1).scene(3).track(1).amp_volume = 100

        # Save
        project.to_directory(temp_dir / "TEST")

        # Other parts should not have the scene lock
        assert project.bank(1).part(2).scene(3).track(1).amp_volume is None

    @pytest.mark.slow
    def test_empty_scenes_not_propagated(self, temp_dir):
        """Scenes without locks should not overwrite target parts."""
        from octapy import Project

        project = Project.from_template("TEST")
        # Set lock only in Part 2, scene 5
        project.bank(1).part(2).scene(5).track(1).amp_volume = 50

        # Save - Part 1's empty scene 5 should NOT overwrite Part 2's
        project.to_directory(temp_dir / "TEST")

        # Part 2's scene 5 should still have its lock
        assert project.bank(1).part(2).scene(5).track(1).amp_volume == 50
