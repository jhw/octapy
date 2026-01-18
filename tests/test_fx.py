"""
Tests for FX module.
"""

import pytest
from octapy import Project
from octapy.api.enums import FX1Type, FX2Type
from octapy.api.fx import (
    BaseFX,
    OffFX,
    FilterFX,
    SpatializerFX,
    DelayFX,
    EqFX,
    DjEqFX,
    PhaserFX,
    FlangerFX,
    ChorusFX,
    CombFilterFX,
    PlateReverbFX,
    SpringReverbFX,
    DarkReverbFX,
    CompressorFX,
    LofiFX,
    create_fx,
)


@pytest.fixture
def project():
    return Project.from_template("TEST")


@pytest.fixture
def track(project):
    return project.bank(1).part(1).track(1)


# =============================================================================
# Factory Tests
# =============================================================================

class TestFXFactory:
    """Test create_fx factory function."""

    def test_create_off_fx(self, track):
        """Test creating OFF FX."""
        fx = create_fx(track, slot=1, fx_type=FX1Type.OFF)
        assert isinstance(fx, OffFX)

    def test_create_filter_fx(self, track):
        """Test creating Filter FX."""
        fx = create_fx(track, slot=1, fx_type=FX1Type.FILTER)
        assert isinstance(fx, FilterFX)

    def test_create_delay_fx(self, track):
        """Test creating Delay FX (FX2 only)."""
        fx = create_fx(track, slot=2, fx_type=FX2Type.DELAY)
        assert isinstance(fx, DelayFX)

    def test_create_plate_reverb_fx(self, track):
        """Test creating Plate Reverb FX (FX2 only)."""
        fx = create_fx(track, slot=2, fx_type=FX2Type.PLATE_REVERB)
        assert isinstance(fx, PlateReverbFX)

    def test_unknown_type_returns_off(self, track):
        """Test unknown FX type returns OffFX."""
        fx = create_fx(track, slot=1, fx_type=999)
        assert isinstance(fx, OffFX)


# =============================================================================
# Part Track Integration Tests
# =============================================================================

class TestPartTrackFX:
    """Test FX access via AudioPartTrack."""

    def test_fx1_returns_correct_type(self, track):
        """Test fx1 property returns correct FX type."""
        track.fx1_type = FX1Type.FILTER
        assert isinstance(track.fx1, FilterFX)

    def test_fx2_returns_correct_type(self, track):
        """Test fx2 property returns correct FX type."""
        track.fx2_type = FX2Type.DELAY
        assert isinstance(track.fx2, DelayFX)

    def test_fx1_type_change_updates_container(self, track):
        """Test changing fx1_type changes the container type."""
        track.fx1_type = FX1Type.FILTER
        assert isinstance(track.fx1, FilterFX)

        track.fx1_type = FX1Type.COMPRESSOR
        assert isinstance(track.fx1, CompressorFX)

    def test_fx_default_type_is_filter(self, track):
        """Test default FX1 type is FILTER."""
        # Default should be FILTER (value 4)
        assert track.fx1_type == FX1Type.FILTER
        assert isinstance(track.fx1, FilterFX)

    def test_fx2_default_type_is_delay(self, track):
        """Test default FX2 type is DELAY."""
        # Default should be DELAY (value 8)
        assert track.fx2_type == FX2Type.DELAY
        assert isinstance(track.fx2, DelayFX)


# =============================================================================
# Filter FX Tests
# =============================================================================

class TestFilterFX:
    """Test FilterFX properties."""

    def test_filter_base(self, track):
        """Test filter base property."""
        track.fx1_type = FX1Type.FILTER
        track.fx1.base = 64
        assert track.fx1.base == 64

    def test_filter_width(self, track):
        """Test filter width property."""
        track.fx1_type = FX1Type.FILTER
        track.fx1.width = 80
        assert track.fx1.width == 80

    def test_filter_q(self, track):
        """Test filter Q property."""
        track.fx1_type = FX1Type.FILTER
        track.fx1.q = 100
        assert track.fx1.q == 100

    def test_filter_depth(self, track):
        """Test filter depth property."""
        track.fx1_type = FX1Type.FILTER
        track.fx1.depth = 50
        assert track.fx1.depth == 50

    def test_filter_attack(self, track):
        """Test filter attack property."""
        track.fx1_type = FX1Type.FILTER
        track.fx1.attack = 30
        assert track.fx1.attack == 30

    def test_filter_decay(self, track):
        """Test filter decay property."""
        track.fx1_type = FX1Type.FILTER
        track.fx1.decay = 70
        assert track.fx1.decay == 70


# =============================================================================
# Delay FX Tests
# =============================================================================

class TestDelayFX:
    """Test DelayFX properties."""

    def test_delay_time(self, track):
        """Test delay time property."""
        track.fx2_type = FX2Type.DELAY
        track.fx2.time = 64
        assert track.fx2.time == 64

    def test_delay_feedback(self, track):
        """Test delay feedback property."""
        track.fx2_type = FX2Type.DELAY
        track.fx2.feedback = 80
        assert track.fx2.feedback == 80

    def test_delay_volume(self, track):
        """Test delay volume property."""
        track.fx2_type = FX2Type.DELAY
        track.fx2.volume = 100
        assert track.fx2.volume == 100

    def test_delay_send(self, track):
        """Test delay send property."""
        track.fx2_type = FX2Type.DELAY
        track.fx2.send = 64
        assert track.fx2.send == 64


# =============================================================================
# Reverb FX Tests
# =============================================================================

class TestReverbFX:
    """Test Reverb FX properties."""

    def test_plate_reverb_time(self, track):
        """Test plate reverb time property."""
        track.fx2_type = FX2Type.PLATE_REVERB
        track.fx2.time = 80
        assert track.fx2.time == 80

    def test_plate_reverb_damp(self, track):
        """Test plate reverb damp property."""
        track.fx2_type = FX2Type.PLATE_REVERB
        track.fx2.damp = 50
        assert track.fx2.damp == 50

    def test_plate_reverb_mix(self, track):
        """Test plate reverb mix property."""
        track.fx2_type = FX2Type.PLATE_REVERB
        track.fx2.mix = 64
        assert track.fx2.mix == 64

    def test_spring_reverb_time(self, track):
        """Test spring reverb time property."""
        track.fx2_type = FX2Type.SPRING_REVERB
        track.fx2.time = 70
        assert track.fx2.time == 70

    def test_dark_reverb_shug(self, track):
        """Test dark reverb shug property."""
        track.fx2_type = FX2Type.DARK_REVERB
        track.fx2.shug = 60
        assert track.fx2.shug == 60


# =============================================================================
# Compressor FX Tests
# =============================================================================

class TestCompressorFX:
    """Test CompressorFX properties."""

    def test_compressor_attack(self, track):
        """Test compressor attack property."""
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.attack = 20
        assert track.fx1.attack == 20

    def test_compressor_release(self, track):
        """Test compressor release property."""
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.release = 50
        assert track.fx1.release == 50

    def test_compressor_threshold(self, track):
        """Test compressor threshold property."""
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.threshold = 64
        assert track.fx1.threshold == 64

    def test_compressor_ratio(self, track):
        """Test compressor ratio property."""
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.ratio = 80
        assert track.fx1.ratio == 80

    def test_compressor_gain(self, track):
        """Test compressor gain property."""
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.gain = 48
        assert track.fx1.gain == 48

    def test_compressor_mix(self, track):
        """Test compressor mix property."""
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.mix = 127
        assert track.fx1.mix == 127


# =============================================================================
# EQ FX Tests
# =============================================================================

class TestEqFX:
    """Test EQ FX properties."""

    def test_eq_freq1(self, track):
        """Test EQ freq1 property."""
        track.fx1_type = FX1Type.EQ
        track.fx1.freq1 = 64
        assert track.fx1.freq1 == 64

    def test_eq_gain1(self, track):
        """Test EQ gain1 property."""
        track.fx1_type = FX1Type.EQ
        track.fx1.gain1 = 80
        assert track.fx1.gain1 == 80

    def test_dj_eq_low_gain(self, track):
        """Test DJ EQ low_gain property."""
        track.fx1_type = FX1Type.DJ_EQ
        track.fx1.low_gain = 64
        assert track.fx1.low_gain == 64

    def test_dj_eq_mid_gain(self, track):
        """Test DJ EQ mid_gain property."""
        track.fx1_type = FX1Type.DJ_EQ
        track.fx1.mid_gain = 64
        assert track.fx1.mid_gain == 64

    def test_dj_eq_high_gain(self, track):
        """Test DJ EQ high_gain property."""
        track.fx1_type = FX1Type.DJ_EQ
        track.fx1.high_gain = 100
        assert track.fx1.high_gain == 100


# =============================================================================
# Modulation FX Tests
# =============================================================================

class TestModulationFX:
    """Test Modulation FX properties."""

    def test_phaser_center(self, track):
        """Test phaser center property."""
        track.fx1_type = FX1Type.PHASER
        track.fx1.center = 64
        assert track.fx1.center == 64

    def test_phaser_mix(self, track):
        """Test phaser mix property."""
        track.fx1_type = FX1Type.PHASER
        track.fx1.mix = 80
        assert track.fx1.mix == 80

    def test_flanger_delay(self, track):
        """Test flanger delay property."""
        track.fx1_type = FX1Type.FLANGER
        track.fx1.delay = 50
        assert track.fx1.delay == 50

    def test_chorus_depth(self, track):
        """Test chorus depth property."""
        track.fx1_type = FX1Type.CHORUS
        track.fx1.depth = 70
        assert track.fx1.depth == 70

    def test_comb_filter_pitch(self, track):
        """Test comb filter pitch property."""
        track.fx1_type = FX1Type.COMB_FILTER
        track.fx1.pitch = 64
        assert track.fx1.pitch == 64


# =============================================================================
# Other FX Tests
# =============================================================================

class TestOtherFX:
    """Test other FX types."""

    def test_spatializer_width(self, track):
        """Test spatializer width property."""
        track.fx1_type = FX1Type.SPATIALIZER
        track.fx1.width = 100
        assert track.fx1.width == 100

    def test_lofi_dist(self, track):
        """Test lofi dist property."""
        track.fx1_type = FX1Type.LOFI
        track.fx1.dist = 64
        assert track.fx1.dist == 64

    def test_lofi_srr(self, track):
        """Test lofi srr (sample rate reduction) property."""
        track.fx1_type = FX1Type.LOFI
        track.fx1.srr = 80
        assert track.fx1.srr == 80


# =============================================================================
# Multi-Track Tests
# =============================================================================

class TestMultiTrackFX:
    """Test FX across multiple tracks."""

    def test_fx_independent_per_track(self, project):
        """Test FX parameters are independent per track."""
        part = project.bank(1).part(1)

        # Set different FX types on different tracks
        part.track(1).fx1_type = FX1Type.FILTER
        part.track(2).fx1_type = FX1Type.COMPRESSOR

        # Set values
        part.track(1).fx1.base = 100
        part.track(2).fx1.attack = 50

        # Verify independence
        assert part.track(1).fx1.base == 100
        assert part.track(2).fx1.attack == 50
        assert isinstance(part.track(1).fx1, FilterFX)
        assert isinstance(part.track(2).fx1, CompressorFX)

    def test_fx1_fx2_independent(self, track):
        """Test FX1 and FX2 are independent."""
        track.fx1_type = FX1Type.FILTER
        track.fx2_type = FX2Type.DELAY

        track.fx1.base = 80
        track.fx2.time = 64

        assert track.fx1.base == 80
        assert track.fx2.time == 64


# =============================================================================
# Roundtrip Tests
# =============================================================================

class TestFXRoundtrip:
    """Test FX parameters survive save/load."""

    @pytest.mark.slow
    def test_fx_parameters_roundtrip(self, project, temp_dir):
        """Test FX parameters survive save/load."""
        track = project.bank(1).part(1).track(1)

        # Set FX1 to compressor with all params
        track.fx1_type = FX1Type.COMPRESSOR
        track.fx1.attack = 20
        track.fx1.release = 50
        track.fx1.threshold = 64
        track.fx1.ratio = 80
        track.fx1.gain = 48
        track.fx1.mix = 100

        # Set FX2 to delay with all params
        track.fx2_type = FX2Type.DELAY
        track.fx2.time = 64
        track.fx2.feedback = 80
        track.fx2.volume = 100
        track.fx2.send = 64

        # Save and reload
        project.to_directory(temp_dir / "TEST")
        loaded = Project.from_directory(temp_dir / "TEST")
        loaded_track = loaded.bank(1).part(1).track(1)

        # Verify FX1 (compressor)
        assert loaded_track.fx1_type == FX1Type.COMPRESSOR
        assert loaded_track.fx1.attack == 20
        assert loaded_track.fx1.release == 50
        assert loaded_track.fx1.threshold == 64
        assert loaded_track.fx1.ratio == 80
        assert loaded_track.fx1.gain == 48
        assert loaded_track.fx1.mix == 100

        # Verify FX2 (delay)
        assert loaded_track.fx2_type == FX2Type.DELAY
        assert loaded_track.fx2.time == 64
        assert loaded_track.fx2.feedback == 80
        assert loaded_track.fx2.volume == 100
        assert loaded_track.fx2.send == 64
