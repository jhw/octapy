"""
Tests for Scene module.
"""

import pytest
from octapy import Project
from octapy.api.scene import (
    Scene,
    AudioSceneTrack,
    SamplerSceneTrack,
    ThruSceneTrack,
    NeighborSceneTrack,
    PickupSceneTrack,
)


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

class TestSceneTrackAccess:
    """Test scene track access."""

    def test_track_access(self, scene):
        """Test accessing a track from a scene."""
        track = scene.track(1)
        assert isinstance(track, AudioSceneTrack)

    def test_sampler_track_access(self, scene):
        """Test accessing a sampler track."""
        track = scene.sampler_track(1)
        assert isinstance(track, SamplerSceneTrack)

    def test_thru_track_access(self, scene):
        """Test accessing a thru track."""
        track = scene.thru_track(1)
        assert isinstance(track, ThruSceneTrack)

    def test_neighbor_track_access(self, scene):
        """Test accessing a neighbor track."""
        track = scene.neighbor_track(1)
        assert isinstance(track, NeighborSceneTrack)

    def test_pickup_track_access(self, scene):
        """Test accessing a pickup track."""
        track = scene.pickup_track(1)
        assert isinstance(track, PickupSceneTrack)

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

    def test_sampler_playback_defaults_none(self, scene):
        """Test sampler playback params default to None (no lock)."""
        track = scene.sampler_track(1)
        assert track.pitch is None
        assert track.start is None
        assert track.length is None
        assert track.rate is None
        assert track.retrig is None
        assert track.retrig_time is None


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

class TestSamplerPlaybackLocks:
    """Test Sampler playback page locks."""

    def test_pitch(self, scene):
        """Test pitch lock."""
        track = scene.sampler_track(1)
        track.pitch = 72
        assert track.pitch == 72

    def test_start(self, scene):
        """Test start lock."""
        track = scene.sampler_track(1)
        track.start = 32
        assert track.start == 32

    def test_length(self, scene):
        """Test length lock."""
        track = scene.sampler_track(1)
        track.length = 127
        assert track.length == 127

    def test_rate(self, scene):
        """Test rate lock."""
        track = scene.sampler_track(1)
        track.rate = 64
        assert track.rate == 64

    def test_retrig(self, scene):
        """Test retrig lock."""
        track = scene.sampler_track(1)
        track.retrig = 4
        assert track.retrig == 4

    def test_retrig_time(self, scene):
        """Test retrig time lock."""
        track = scene.sampler_track(1)
        track.retrig_time = 79
        assert track.retrig_time == 79


# =============================================================================
# Thru Playback Lock Tests
# =============================================================================

class TestThruPlaybackLocks:
    """Test Thru playback page locks."""

    def test_in_ab(self, scene):
        """Test in_ab lock."""
        track = scene.thru_track(1)
        track.in_ab = 1
        assert track.in_ab == 1

    def test_vol_ab(self, scene):
        """Test vol_ab lock."""
        track = scene.thru_track(1)
        track.vol_ab = 64
        assert track.vol_ab == 64

    def test_in_cd(self, scene):
        """Test in_cd lock."""
        track = scene.thru_track(1)
        track.in_cd = 2
        assert track.in_cd == 2

    def test_vol_cd(self, scene):
        """Test vol_cd lock."""
        track = scene.thru_track(1)
        track.vol_cd = 80
        assert track.vol_cd == 80


# =============================================================================
# Neighbor Lock Tests
# =============================================================================

class TestNeighborLocks:
    """Test Neighbor scene locks (AMP/FX only, no playback)."""

    def test_neighbor_amp_locks(self, scene):
        """Test neighbor AMP locks work."""
        track = scene.neighbor_track(1)
        track.amp_volume = 100
        track.amp_balance = 32
        assert track.amp_volume == 100
        assert track.amp_balance == 32

    def test_neighbor_fx_locks(self, scene):
        """Test neighbor FX locks work."""
        track = scene.neighbor_track(1)
        track.fx1_param1 = 64
        track.fx2_param1 = 80
        assert track.fx1_param1 == 64
        assert track.fx2_param1 == 80


# =============================================================================
# Pickup Playback Lock Tests
# =============================================================================

class TestPickupPlaybackLocks:
    """Test Pickup playback page locks."""

    def test_pitch(self, scene):
        """Test pitch lock."""
        track = scene.pickup_track(1)
        track.pitch = 64
        assert track.pitch == 64

    def test_direction(self, scene):
        """Test direction lock."""
        track = scene.pickup_track(1)
        track.direction = 2
        assert track.direction == 2

    def test_length(self, scene):
        """Test length lock."""
        track = scene.pickup_track(1)
        track.length = 1
        assert track.length == 1

    def test_gain(self, scene):
        """Test gain lock."""
        track = scene.pickup_track(1)
        track.gain = 80
        assert track.gain == 80

    def test_operation(self, scene):
        """Test operation lock."""
        track = scene.pickup_track(1)
        track.operation = 1
        assert track.operation == 1


# =============================================================================
# Clear All Locks Tests
# =============================================================================

class TestClearAllLocks:
    """Test clearing all locks."""

    def test_clear_track_locks(self, scene):
        """Test clearing all locks for a track."""
        track = scene.sampler_track(1)

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
        scene.sampler_track(3).pitch = 72

        # Clear all
        scene.clear_all_locks()

        # Verify all cleared
        assert scene.track(1).amp_volume is None
        assert scene.track(2).amp_volume is None
        assert scene.sampler_track(3).pitch is None


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
# Roundtrip Tests
# =============================================================================

class TestSceneRoundtrip:
    """Test scene locks survive save/load."""

    @pytest.mark.slow
    def test_scene_locks_roundtrip(self, project, temp_dir):
        """Test scene locks survive save/load."""
        part = project.bank(1).part(1)
        scene = part.scene(1)

        # Set various locks
        scene.track(1).amp_volume = 100
        scene.track(1).amp_attack = 32
        scene.track(1).fx1_param1 = 64
        scene.track(1).fx2_param3 = 80

        scene.sampler_track(2).pitch = 72
        scene.sampler_track(2).start = 16
        scene.sampler_track(2).length = 127

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
        assert loaded_scene.sampler_track(2).pitch == 72
        assert loaded_scene.sampler_track(2).start == 16
        assert loaded_scene.sampler_track(2).length == 127

        # Verify unlocked params are still None
        assert loaded_scene.track(3).amp_volume is None
