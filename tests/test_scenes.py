"""
Tests for Scene module.
"""

import pytest
from octapy import Project, Scene, AudioSceneTrack


@pytest.fixture
def project():
    return Project.from_template("TEST")


@pytest.fixture
def part(project):
    return project.bank(1).part(1)


@pytest.fixture
def scene(part):
    return part.scene(1)


# =============================================================================
# Scene Access Tests
# =============================================================================

class TestSceneAccess:
    """Test scene access from Part."""

    def test_scene_access(self, part):
        """Test accessing a scene from a part."""
        scene = part.scene(1)
        assert isinstance(scene, Scene)

    def test_scene_range(self, part):
        """Test all 16 scenes are accessible."""
        for i in range(1, 17):
            scene = part.scene(i)
            assert isinstance(scene, Scene)

    def test_scene_caching(self, part):
        """Test scene instances are cached."""
        scene1 = part.scene(1)
        scene2 = part.scene(1)
        assert scene1 is scene2


# =============================================================================
# Scene Track Access Tests
# =============================================================================

class TestAudioSceneTrackAccess:
    """Test scene track access."""

    def test_track_access(self, scene):
        """Test accessing a track from a scene."""
        track = scene.track(1)
        assert isinstance(track, AudioSceneTrack)

    def test_track_range(self, scene):
        """Test all 8 tracks are accessible."""
        for i in range(1, 9):
            track = scene.track(i)
            assert isinstance(track, AudioSceneTrack)

    def test_track_caching(self, scene):
        """Test track instances are cached."""
        track1 = scene.track(1)
        track2 = scene.track(1)
        assert track1 is track2


# =============================================================================
# Default Values Tests
# =============================================================================

class TestDefaultValues:
    """Test default scene lock values (None = no lock)."""

    def test_amp_defaults_none(self, scene):
        """Test AMP params default to None (no lock)."""
        track = scene.track(1)
        assert track.amp_attack is None
        assert track.amp_hold is None
        assert track.amp_release is None
        assert track.amp_volume is None
        assert track.amp_balance is None

    def test_fx1_defaults_none(self, scene):
        """Test FX1 params default to None (no lock)."""
        track = scene.track(1)
        assert track.fx1_param1 is None
        assert track.fx1_param2 is None
        assert track.fx1_param3 is None
        assert track.fx1_param4 is None
        assert track.fx1_param5 is None
        assert track.fx1_param6 is None

    def test_fx2_defaults_none(self, scene):
        """Test FX2 params default to None (no lock)."""
        track = scene.track(1)
        assert track.fx2_param1 is None
        assert track.fx2_param2 is None
        assert track.fx2_param3 is None
        assert track.fx2_param4 is None
        assert track.fx2_param5 is None
        assert track.fx2_param6 is None

    def test_playback_defaults_none(self, scene):
        """Test playback params default to None (no lock)."""
        track = scene.track(1)
        assert track.pitch is None
        assert track.start is None
        assert track.length is None
        assert track.rate is None


# =============================================================================
# AMP Lock Tests
# =============================================================================

class TestAmpLocks:
    """Test AMP page locks."""

    def test_amp_attack(self, scene):
        """Test AMP attack lock."""
        track = scene.track(1)
        track.amp_attack = 64
        assert track.amp_attack == 64

    def test_amp_hold(self, scene):
        """Test AMP hold lock."""
        track = scene.track(1)
        track.amp_hold = 100
        assert track.amp_hold == 100

    def test_amp_release(self, scene):
        """Test AMP release lock."""
        track = scene.track(1)
        track.amp_release = 80
        assert track.amp_release == 80

    def test_amp_volume(self, scene):
        """Test AMP volume lock."""
        track = scene.track(1)
        track.amp_volume = 127
        assert track.amp_volume == 127

    def test_amp_balance(self, scene):
        """Test AMP balance lock."""
        track = scene.track(1)
        track.amp_balance = 64
        assert track.amp_balance == 64

    def test_clear_amp_lock(self, scene):
        """Test clearing an AMP lock."""
        track = scene.track(1)
        track.amp_volume = 100
        assert track.amp_volume == 100
        track.amp_volume = None
        assert track.amp_volume is None


# =============================================================================
# FX Lock Tests
# =============================================================================

class TestFxLocks:
    """Test FX page locks."""

    def test_fx1_params(self, scene):
        """Test FX1 param locks."""
        track = scene.track(1)
        track.fx1_param1 = 10
        track.fx1_param2 = 20
        track.fx1_param3 = 30
        track.fx1_param4 = 40
        track.fx1_param5 = 50
        track.fx1_param6 = 60
        assert track.fx1_param1 == 10
        assert track.fx1_param2 == 20
        assert track.fx1_param3 == 30
        assert track.fx1_param4 == 40
        assert track.fx1_param5 == 50
        assert track.fx1_param6 == 60

    def test_fx2_params(self, scene):
        """Test FX2 param locks."""
        track = scene.track(1)
        track.fx2_param1 = 15
        track.fx2_param2 = 25
        track.fx2_param3 = 35
        track.fx2_param4 = 45
        track.fx2_param5 = 55
        track.fx2_param6 = 65
        assert track.fx2_param1 == 15
        assert track.fx2_param2 == 25
        assert track.fx2_param3 == 35
        assert track.fx2_param4 == 45
        assert track.fx2_param5 == 55
        assert track.fx2_param6 == 65


# =============================================================================
# Sampler Playback Lock Tests
# =============================================================================

class TestPlaybackLocks:
    """Test playback page locks."""

    def test_pitch(self, scene):
        """Test pitch lock."""
        track = scene.track(1)
        track.pitch = 72
        assert track.pitch == 72

    def test_start(self, scene):
        """Test start lock."""
        track = scene.track(1)
        track.start = 32
        assert track.start == 32

    def test_slice_index(self, scene):
        """Test slice_index lock encodes as raw STRT value * 2."""
        track = scene.track(1)
        track.slice_index = 3
        assert track.slice_index == 3
        # Raw STRT value should be slice_index * 2
        assert track.start == 6

    def test_slice_index_zero(self, scene):
        """Test slice_index 0 maps to raw STRT 0."""
        track = scene.track(1)
        track.slice_index = 0
        assert track.slice_index == 0
        assert track.start == 0

    def test_slice_index_none_clears(self, scene):
        """Test setting slice_index to None clears the lock."""
        track = scene.track(1)
        track.slice_index = 5
        assert track.slice_index == 5
        track.slice_index = None
        assert track.slice_index is None

    def test_length(self, scene):
        """Test length lock."""
        track = scene.track(1)
        track.length = 127
        assert track.length == 127

    def test_rate(self, scene):
        """Test rate lock."""
        track = scene.track(1)
        track.rate = 64
        assert track.rate == 64


# =============================================================================
# Playback Parameter Lock Tests
# =============================================================================

class TestPlaybackParamLocks:
    """Test playback parameter locks (generic params 1-6)."""

    def test_playback_param1(self, scene):
        """Test playback param1 lock."""
        track = scene.track(1)
        track.playback_param1 = 64
        assert track.playback_param1 == 64

    def test_playback_param2(self, scene):
        """Test playback param2 lock."""
        track = scene.track(1)
        track.playback_param2 = 80
        assert track.playback_param2 == 80


# =============================================================================
# Clear All Locks Tests
# =============================================================================

class TestClearAllLocks:
    """Test clearing all locks."""

    def test_clear_track_locks(self, scene):
        """Test clearing all locks for a track."""
        track = scene.track(1)

        # Set some locks
        track.pitch = 72
        track.amp_volume = 100
        track.fx1_param1 = 64

        # Clear all
        track.clear_all_locks()

        # Verify all cleared
        assert track.pitch is None
        assert track.amp_volume is None
        assert track.fx1_param1 is None

    def test_clear_scene_locks(self, scene):
        """Test clearing all locks for a scene."""
        # Set locks on multiple tracks
        scene.track(1).amp_volume = 100
        scene.track(2).amp_volume = 80
        scene.track(3).pitch = 72

        # Clear all
        scene.clear_all_locks()

        # Verify all cleared
        assert scene.track(1).amp_volume is None
        assert scene.track(2).amp_volume is None
        assert scene.track(3).pitch is None


# =============================================================================
# Multi-Scene Independence Tests
# =============================================================================

class TestMultiSceneIndependence:
    """Test scenes are independent of each other."""

    def test_scenes_independent(self, part):
        """Test locks in one scene don't affect another."""
        scene1 = part.scene(1)
        scene2 = part.scene(2)

        scene1.track(1).amp_volume = 100
        scene2.track(1).amp_volume = 50

        assert scene1.track(1).amp_volume == 100
        assert scene2.track(1).amp_volume == 50

    def test_tracks_independent(self, scene):
        """Test locks on one track don't affect another."""
        scene.track(1).amp_volume = 100
        scene.track(2).amp_volume = 50

        assert scene.track(1).amp_volume == 100
        assert scene.track(2).amp_volume == 50


# =============================================================================
# Active Scene Tests
# =============================================================================

class TestActiveScenes:
    """Test active scene A/B properties on Part."""

    def test_active_scene_a_default(self, part):
        """Test active scene A default value."""
        # Default is 0 (scene 1)
        assert part.active_scene_a == 0

    def test_active_scene_b_default(self, part):
        """Test active scene B default value."""
        # Default is 8 (scene 9)
        assert part.active_scene_b == 8

    def test_set_active_scene_a(self, part):
        """Test setting active scene A."""
        part.active_scene_a = 5
        assert part.active_scene_a == 5

    def test_set_active_scene_b(self, part):
        """Test setting active scene B."""
        part.active_scene_b = 15
        assert part.active_scene_b == 15


# =============================================================================
# Crossfader (XLV) Tests
# =============================================================================

class TestSceneCrossfader:
    """Tests for Scene.crossfader (XLV) assignments."""

    def test_default_no_assignments(self, scene):
        """A fresh scene has no XLV assignments on any track."""
        assert scene.crossfader_assignments == {}
        for n in range(1, 9):
            assert scene.crossfader(n) is None

    def test_set_and_get_crossfader(self, scene):
        """Setting an XLV value reads back the same value."""
        scene.set_crossfader(1, 64)
        scene.set_crossfader(5, 127)
        scene.set_crossfader(8, 0)
        assert scene.crossfader(1) == 64
        assert scene.crossfader(5) == 127
        assert scene.crossfader(8) == 0
        assert scene.crossfader(2) is None

    def test_set_to_none_clears_assignment(self, scene):
        """Setting XLV to None removes the assignment."""
        scene.set_crossfader(1, 64)
        assert scene.crossfader(1) == 64
        scene.set_crossfader(1, None)
        assert scene.crossfader(1) is None
        assert 1 not in scene.crossfader_assignments

    def test_crossfader_assignments_dict(self, scene):
        """crossfader_assignments returns only set entries."""
        scene.set_crossfader(2, 30)
        scene.set_crossfader(7, 100)
        assert scene.crossfader_assignments == {2: 30, 7: 100}

    def test_invalid_track_number_rejected(self, scene):
        """Track numbers outside 1-8 raise ValueError."""
        with pytest.raises(ValueError):
            scene.crossfader(0)
        with pytest.raises(ValueError):
            scene.crossfader(9)
        with pytest.raises(ValueError):
            scene.set_crossfader(0, 64)
        with pytest.raises(ValueError):
            scene.set_crossfader(9, 64)

    def test_invalid_value_rejected(self, scene):
        """XLV values outside 0-127 raise ValueError."""
        with pytest.raises(ValueError):
            scene.set_crossfader(1, -1)
        with pytest.raises(ValueError):
            scene.set_crossfader(1, 128)

    def test_xlv_affects_is_blank(self, scene):
        """A scene with only XLV assignments is not blank."""
        assert scene.is_blank
        scene.set_crossfader(1, 64)
        assert not scene.is_blank
        scene.set_crossfader(1, None)
        assert scene.is_blank

    def test_xlv_binary_roundtrip(self, project):
        """XLV assignments survive a Part write/read cycle."""
        from octapy._io import BankFile, BankOffset
        from octapy.api.core import Part

        part = project.bank(2).part(1)
        part.scene(5).set_crossfader(2, 100)
        part.scene(5).set_crossfader(7, 0)
        part.scene(10).set_crossfader(1, 64)

        bank = BankFile.new()
        buf = bytearray(bank._data)
        part.write_to_bank(buf, part_offset=BankOffset.PARTS)

        restored = Part.read_from_bank(part_num=1, bank_data=buf, part_offset=BankOffset.PARTS)
        assert restored.scene(5).crossfader_assignments == {2: 100, 7: 0}
        assert restored.scene(10).crossfader_assignments == {1: 64}
        assert restored.scene(1).crossfader_assignments == {}

    def test_xlv_clone(self, scene):
        """XLV assignments survive Scene.clone()."""
        scene.set_crossfader(3, 50)
        cloned = scene.clone()
        assert cloned.crossfader_assignments == {3: 50}
        # Independent buffers
        cloned.set_crossfader(3, 100)
        assert scene.crossfader(3) == 50
        assert cloned.crossfader(3) == 100


# =============================================================================
# Dict round-trip Tests
# =============================================================================

class TestSceneToDict:
    """to_dict / from_dict must round-trip param locks AND XLV.

    Before v0.2.3 to_dict dropped XLV silently — a Scene with only
    crossfader assignments would dump as {scene: N, tracks: []} and
    reload with no XLV at all, so any consumer using these primitives
    to ship scene libraries (e.g. an export pipeline that dumps a
    template's scenes to YAML) lost crossfader morph data.
    """

    def test_param_locks_only(self, scene):
        scene.track(1).amp_volume = 100
        scene.track(2).fx1_param3 = 64
        d = scene.to_dict()
        restored = Scene.from_dict(d)
        assert restored.track(1).amp_volume == 100
        assert restored.track(2).fx1_param3 == 64
        assert restored.crossfader_assignments == {}

    def test_xlv_only(self, scene):
        scene.set_crossfader(1, 0)
        scene.set_crossfader(7, 127)
        d = scene.to_dict()
        assert d["xlv"] == {1: 0, 7: 127}
        restored = Scene.from_dict(d)
        assert restored.crossfader_assignments == {1: 0, 7: 127}

    def test_locks_and_xlv(self, scene):
        scene.track(3).pitch = 72
        scene.set_crossfader(3, 50)
        scene.set_crossfader(8, 110)
        d = scene.to_dict()
        restored = Scene.from_dict(d)
        assert restored.track(3).pitch == 72
        assert restored.crossfader_assignments == {3: 50, 8: 110}

    def test_idempotent(self, scene):
        scene.track(1).amp_attack = 10
        scene.set_crossfader(2, 64)
        d1 = scene.to_dict()
        d2 = Scene.from_dict(d1).to_dict()
        assert d1 == d2

    def test_xlv_omitted_when_empty(self, scene):
        scene.track(1).amp_volume = 100
        d = scene.to_dict()
        assert "xlv" not in d

    def test_xlv_clear_with_none(self, scene):
        """A None value in the xlv dict clears the assignment.

        Mirrors set_crossfader's nullable contract so explicit clears
        survive a round-trip.
        """
        scene.set_crossfader(1, 64)
        restored = Scene.from_dict({"scene": 1, "xlv": {1: None}})
        assert restored.crossfader_assignments == {}


# =============================================================================
# Roundtrip Tests
# =============================================================================

@pytest.mark.slow
class TestSceneRoundtrip:
    """Test scene locks survive save/load."""

    def test_scene_locks_roundtrip(self, project, temp_dir):
        """Test scene locks survive save/load."""
        part = project.bank(1).part(1)
        scene = part.scene(1)

        # Set various locks
        scene.track(1).amp_volume = 100
        scene.track(1).amp_attack = 32
        scene.track(1).fx1_param1 = 64
        scene.track(1).fx2_param3 = 80

        scene.track(2).pitch = 72
        scene.track(2).start = 16
        scene.track(2).length = 127

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")

        loaded_scene = loaded.bank(1).part(1).scene(1)

        # Verify AMP/FX locks
        assert loaded_scene.track(1).amp_volume == 100
        assert loaded_scene.track(1).amp_attack == 32
        assert loaded_scene.track(1).fx1_param1 == 64
        assert loaded_scene.track(1).fx2_param3 == 80

        # Verify playback locks
        assert loaded_scene.track(2).pitch == 72
        assert loaded_scene.track(2).start == 16
        assert loaded_scene.track(2).length == 127

        # Verify unlocked params are still None
        assert loaded_scene.track(3).amp_volume is None
