"""
Tests for to_dict methods across all classes.
"""

import pytest

from octapy import Project, MachineType, TrigCondition


class TestStepToDict:
    """Test Step.to_dict() methods."""

    def test_base_step_to_dict(self):
        """Test BaseStep to_dict returns expected structure."""
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).track(1).step(1)
        result = step.to_dict()

        assert "step" in result
        assert result["step"] == 1
        assert "active" in result
        assert "trigless" in result

    def test_active_step_to_dict(self):
        """Test active step includes correct data."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1]
        step = track.step(1)

        result = step.to_dict()
        assert result["active"] is True
        assert result["trigless"] is False

    def test_step_with_condition_to_dict(self):
        """Test step with condition includes condition name."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1]
        step = track.step(1)
        step.condition = TrigCondition.FILL

        result = step.to_dict()
        assert result["condition"] == "FILL"

    def test_sampler_step_to_dict(self):
        """Test SamplerStep includes volume and pitch."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1]
        step = track.step(1)
        step.volume = 100
        step.pitch = 72

        result = step.to_dict()
        assert result["volume"] == 100
        assert result["pitch"] == 72

    def test_step_with_sample_lock_to_dict(self):
        """Test AudioStep includes sample_lock when set."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1]
        step = track.step(1)
        step.sample_lock = 5

        result = step.to_dict()
        assert "sample_lock" in result
        assert result["sample_lock"] == 5


class TestMidiStepToDict:
    """Test MidiStep.to_dict() method."""

    def test_midi_step_basic_to_dict(self):
        """Test MidiStep to_dict returns expected structure."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        midi_track.active_steps = [1]
        step = midi_track.step(1)

        result = step.to_dict()
        assert "step" in result
        assert "active" in result

    def test_midi_step_with_plocks_to_dict(self):
        """Test MidiStep with p-locks includes note, velocity, length."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        midi_track.active_steps = [1]
        step = midi_track.step(1)
        step.note = 60
        step.velocity = 100
        step.length = 12

        result = step.to_dict()
        assert result["note"] == 60
        assert result["velocity"] == 100
        assert result["length"] == 12


class TestPatternTrackToDict:
    """Test PatternTrack.to_dict() methods."""

    def test_audio_track_to_dict_no_steps(self):
        """Test AudioPatternTrack to_dict without steps."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1, 5, 9, 13]

        result = track.to_dict(include_steps=False)
        assert "track" in result
        assert "active_steps" in result
        assert result["active_steps"] == [1, 5, 9, 13]
        assert "steps" not in result

    def test_audio_track_to_dict_with_steps(self):
        """Test AudioPatternTrack to_dict with steps."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1, 5]

        result = track.to_dict(include_steps=True)
        assert "steps" in result
        assert len(result["steps"]) == 2

    def test_midi_track_to_dict(self):
        """Test MidiPatternTrack to_dict."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        midi_track.active_steps = [1, 2, 3]

        result = midi_track.to_dict()
        assert "track" in result
        assert result["active_steps"] == [1, 2, 3]


class TestPartTrackToDict:
    """Test PartTrack.to_dict() methods."""

    def test_audio_part_track_to_dict(self):
        """Test AudioPartTrack to_dict returns expected structure."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)

        result = track.to_dict()
        assert "track" in result
        assert result["track"] == 1
        assert "machine_type" in result
        assert "flex_slot" in result
        assert "static_slot" in result
        assert "volume" in result
        assert "amp" in result
        assert "fx1_type" in result
        assert "fx2_type" in result

    def test_flex_part_track_to_dict(self):
        """Test AudioPartTrack to_dict includes machine_type and slots."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).audio_track(1)
        track.machine_type = MachineType.FLEX

        result = track.to_dict()
        assert "machine_type" in result
        assert result["machine_type"] == "FLEX"
        assert "flex_slot" in result
        assert "amp" in result

    def test_thru_part_track_to_dict(self):
        """Test AudioPartTrack to_dict with THRU machine type."""
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).audio_track(1)
        track.machine_type = MachineType.THRU

        result = track.to_dict()
        assert result["machine_type"] == "THRU"
        assert "amp" in result
        assert "volume" in result["amp"]

    def test_midi_part_track_to_dict(self):
        """Test MidiPartTrack to_dict returns expected structure."""
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)

        result = midi_track.to_dict()
        assert "track" in result
        assert "channel" in result
        assert "program" in result
        assert "note" in result
        assert "cc" in result
        assert "arp" in result


class TestSceneToDict:
    """Test Scene.to_dict() methods."""

    def test_scene_track_to_dict_empty(self):
        """Test AudioSceneTrack to_dict with no locks."""
        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        track = scene.track(1)

        result = track.to_dict()
        assert "track" in result
        # No other keys if no locks set
        assert "amp" not in result
        assert "fx1" not in result

    def test_scene_track_to_dict_with_locks(self):
        """Test AudioSceneTrack to_dict with locks."""
        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        track = scene.track(1)
        track.amp_volume = 100
        track.fx1_param1 = 64

        result = track.to_dict()
        assert "amp" in result
        assert result["amp"]["volume"] == 100
        assert "fx1" in result
        assert result["fx1"]["param1"] == 64

    def test_scene_track_playback_to_dict(self):
        """Test SceneTrack to_dict includes playback locks."""
        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        track = scene.track(1)
        track.pitch = 72  # Maps to playback_param1
        track.start = 32  # Maps to playback_param2

        result = track.to_dict()
        assert "playback" in result
        # SceneTrack uses generic param names since it doesn't know machine type
        assert result["playback"]["param1"] == 72
        assert result["playback"]["param2"] == 32

    def test_scene_to_dict(self):
        """Test Scene container to_dict."""
        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)
        scene.track(1).amp_volume = 100

        result = scene.to_dict()
        assert "scene" in result
        assert result["scene"] == 1
        assert "tracks" in result
        assert len(result["tracks"]) == 1  # Only track with locks


class TestPartToDict:
    """Test Part.to_dict() method."""

    def test_part_to_dict_basic(self):
        """Test Part to_dict returns expected structure."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)

        result = part.to_dict()
        assert "part" in result
        assert result["part"] == 1
        assert "active_scene_a" in result
        assert "active_scene_b" in result
        assert "audio_tracks" in result
        assert "midi_tracks" in result
        assert len(result["audio_tracks"]) == 8
        assert len(result["midi_tracks"]) == 8

    def test_part_to_dict_with_scenes(self):
        """Test Part to_dict with include_scenes."""
        project = Project.from_template("TEST")
        part = project.bank(1).part(1)
        part.scene(1).track(1).amp_volume = 100

        result = part.to_dict(include_scenes=True)
        assert "scenes" in result
        assert len(result["scenes"]) == 1  # Only scene with locks


class TestPatternToDict:
    """Test Pattern.to_dict() method."""

    def test_pattern_to_dict_basic(self):
        """Test Pattern to_dict returns expected structure."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)

        result = pattern.to_dict()
        assert "pattern" in result
        assert result["pattern"] == 1
        assert "part" in result
        assert "audio_tracks" in result
        assert "midi_tracks" in result
        assert len(result["audio_tracks"]) == 8
        assert len(result["midi_tracks"]) == 8

    def test_pattern_to_dict_with_steps(self):
        """Test Pattern to_dict with include_steps."""
        project = Project.from_template("TEST")
        pattern = project.bank(1).pattern(1)
        pattern.track(1).active_steps = [1, 5, 9]

        result = pattern.to_dict(include_steps=True)
        # First track should have steps
        assert "steps" in result["audio_tracks"][0]
        assert len(result["audio_tracks"][0]["steps"]) == 3


class TestBankToDict:
    """Test Bank.to_dict() method."""

    def test_bank_to_dict_basic(self):
        """Test Bank to_dict returns expected structure."""
        project = Project.from_template("TEST")
        bank = project.bank(1)

        result = bank.to_dict()
        assert "bank" in result
        assert result["bank"] == 1
        assert "flex_count" in result
        assert "parts" in result
        assert "patterns" in result
        assert len(result["parts"]) == 4
        assert len(result["patterns"]) == 16

    def test_bank_to_dict_with_options(self):
        """Test Bank to_dict with include_steps and include_scenes."""
        project = Project.from_template("TEST")
        bank = project.bank(1)
        bank.pattern(1).track(1).active_steps = [1]
        bank.part(1).scene(1).track(1).amp_volume = 100

        result = bank.to_dict(include_steps=True, include_scenes=True)
        # Check steps included in pattern
        assert "steps" in result["patterns"][0]["audio_tracks"][0]
        # Check scenes included in part
        assert "scenes" in result["parts"][0]


class TestProjectToDict:
    """Test Project.to_dict() method."""

    def test_project_to_dict_basic(self):
        """Test Project to_dict returns expected structure."""
        project = Project.from_template("TEST")

        result = project.to_dict()
        assert "name" in result
        assert result["name"] == "TEST"
        assert "tempo" in result
        assert "flex_slot_count" in result
        assert "static_slot_count" in result
        assert "banks" in result
        assert len(result["banks"]) == 16

    def test_project_to_dict_with_steps(self):
        """Test Project to_dict includes step data when requested."""
        project = Project.from_template("TEST")
        project.bank(1).pattern(1).track(1).active_steps = [1, 5]

        result = project.to_dict(include_steps=True)
        assert "banks" in result
        # Find the pattern with step data
        bank1 = result["banks"][0]
        pattern1 = bank1["patterns"][0]
        # Should have audio_tracks
        assert "audio_tracks" in pattern1

    def test_project_to_dict_with_scenes(self):
        """Test Project to_dict includes scene data when requested."""
        project = Project.from_template("TEST")
        project.bank(1).part(1).scene(1).track(1).amp_volume = 100

        result = project.to_dict(include_scenes=True)
        bank1 = result["banks"][0]
        part1 = bank1["parts"][0]
        assert "scenes" in part1

    def test_project_to_dict_full(self):
        """Test Project to_dict with all options."""
        project = Project.from_template("TEST")
        project.bank(1).pattern(1).track(1).active_steps = [1, 5]
        project.bank(1).part(1).scene(1).track(1).amp_volume = 100

        result = project.to_dict(include_steps=True, include_scenes=True)
        assert "banks" in result
        # Check nested data is present
        first_bank = result["banks"][0]
        first_pattern = first_bank["patterns"][0]
        first_track = first_pattern["audio_tracks"][0]
        assert "steps" in first_track
        assert len(first_track["steps"]) == 2


class TestToDictConsistency:
    """Test to_dict consistency and data integrity."""

    def test_step_data_roundtrip(self):
        """Test step data is correctly represented in to_dict."""
        project = Project.from_template("TEST")
        track = project.bank(1).pattern(1).track(1)
        track.active_steps = [1, 5, 9, 13]

        step1 = track.step(1)
        step1.condition = TrigCondition.PRE
        step1.volume = 90

        step5 = track.step(5)
        step5.condition = TrigCondition.FILL
        step5.pitch = 72

        result = track.to_dict(include_steps=True)

        # Find step 1 and step 5 in results
        steps_by_num = {s["step"]: s for s in result["steps"]}

        assert steps_by_num[1]["condition"] == "PRE"
        assert steps_by_num[1]["volume"] == 90
        assert steps_by_num[5]["condition"] == "FILL"
        assert steps_by_num[5]["pitch"] == 72

    def test_scene_locks_represented(self):
        """Test scene locks are correctly represented."""
        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)

        # Set some locks
        scene.track(1).amp_volume = 100
        scene.track(1).amp_attack = 32
        scene.track(2).fx1_param1 = 64

        result = scene.to_dict()
        tracks_by_num = {t["track"]: t for t in result["tracks"]}

        assert tracks_by_num[1]["amp"]["volume"] == 100
        assert tracks_by_num[1]["amp"]["attack"] == 32
        assert tracks_by_num[2]["fx1"]["param1"] == 64

    def test_empty_collections_not_included(self):
        """Test empty collections are not included in output."""
        project = Project.from_template("TEST")
        scene = project.bank(1).part(1).scene(1)

        # No locks set
        result = scene.to_dict()
        assert result["tracks"] == []  # Empty, but key present
