"""
Tests for p-locks (parameter locks) and trig conditions.
"""

import pytest

from octapy import BankFile, Pattern, AudioTrack, TrigCondition, PlockOffset


class TestAudioTrackVolumePlock:
    """AudioTrack volume p-lock tests."""

    def test_default_volume_is_none(self, bank_file):
        """Test that default volume p-lock is None (disabled)."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        # All steps should have no volume p-lock by default
        for step in range(1, 17):
            assert track.get_volume(step) is None

    def test_set_volume_plock(self, bank_file):
        """Test setting a volume p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_volume(step=1, value=100)
        assert track.get_volume(1) == 100

    def test_set_volume_plock_clamps_to_127(self, bank_file):
        """Test that volume values are clamped to 127."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_volume(step=1, value=200)
        assert track.get_volume(1) <= 127

    def test_clear_volume_plock(self, bank_file):
        """Test clearing a volume p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_volume(step=1, value=100)
        track.set_volume(step=1, value=None)
        assert track.get_volume(1) is None

    def test_volume_plocks_independent_per_step(self, bank_file):
        """Test that volume p-locks are independent per step."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_volume(step=1, value=50)
        track.set_volume(step=5, value=100)
        track.set_volume(step=9, value=75)

        assert track.get_volume(1) == 50
        assert track.get_volume(5) == 100
        assert track.get_volume(9) == 75
        assert track.get_volume(2) is None


class TestAudioTrackPitchPlock:
    """AudioTrack pitch p-lock tests."""

    def test_default_pitch_is_none(self, bank_file):
        """Test that default pitch p-lock is None (disabled)."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        for step in range(1, 17):
            assert track.get_pitch(step) is None

    def test_set_pitch_plock(self, bank_file):
        """Test setting a pitch p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_pitch(step=1, value=64)  # Center pitch
        assert track.get_pitch(1) == 64

    def test_pitch_range(self, bank_file):
        """Test pitch values across range."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        # Low pitch
        track.set_pitch(step=1, value=0)
        assert track.get_pitch(1) == 0

        # High pitch
        track.set_pitch(step=2, value=127)
        assert track.get_pitch(2) == 127


class TestAudioTrackTrigCondition:
    """AudioTrack trig condition tests."""

    def test_default_condition_is_none(self, bank_file):
        """Test that default trig condition is NONE."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        for step in range(1, 17):
            assert track.get_trig_condition(step) == TrigCondition.NONE

    def test_set_fill_condition(self, bank_file):
        """Test setting FILL condition."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_trig_condition(step=1, condition=TrigCondition.FILL)
        assert track.get_trig_condition(1) == TrigCondition.FILL

    def test_set_probability_condition(self, bank_file):
        """Test setting probability conditions."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_trig_condition(step=1, condition=TrigCondition.PERCENT_50)
        assert track.get_trig_condition(1) == TrigCondition.PERCENT_50

        track.set_trig_condition(step=2, condition=TrigCondition.PERCENT_75)
        assert track.get_trig_condition(2) == TrigCondition.PERCENT_75

    def test_set_pattern_loop_condition(self, bank_file):
        """Test setting pattern loop conditions."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        # Trigger on loop 1, reset every 4 loops
        track.set_trig_condition(step=1, condition=TrigCondition.T1_R4)
        assert track.get_trig_condition(1) == TrigCondition.T1_R4

    def test_set_condition_with_int(self, bank_file):
        """Test setting condition using raw integer value."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_trig_condition(step=1, condition=19)  # PERCENT_50
        assert track.get_trig_condition(1) == TrigCondition.PERCENT_50


class TestAudioTrackTrigRepeat:
    """AudioTrack trig repeat tests."""

    def test_default_repeat_is_one(self, bank_file):
        """Test that default trig repeat is 1 (no repeat)."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        for step in range(1, 17):
            assert track.get_trig_repeat(step) == 1

    def test_set_trig_repeat(self, bank_file):
        """Test setting trig repeat count."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_trig_repeat(step=1, count=4)
        assert track.get_trig_repeat(1) == 4

    def test_trig_repeat_range(self, bank_file):
        """Test trig repeat across full range (1-8)."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        for count in range(1, 9):
            track.set_trig_repeat(step=count, count=count)
            assert track.get_trig_repeat(count) == count

    def test_invalid_repeat_raises(self, bank_file):
        """Test that invalid repeat values raise ValueError."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        with pytest.raises(ValueError):
            track.set_trig_repeat(step=1, count=0)

        with pytest.raises(ValueError):
            track.set_trig_repeat(step=1, count=9)


class TestPatternPlockConvenience:
    """Pattern-level p-lock convenience method tests."""

    def test_pattern_set_volume(self, bank_file):
        """Test Pattern.set_volume convenience method."""
        pattern = bank_file.get_pattern(1)

        pattern.set_volume(track=1, step=1, value=100)
        assert pattern.get_volume(track=1, step=1) == 100

    def test_pattern_set_pitch(self, bank_file):
        """Test Pattern.set_pitch convenience method."""
        pattern = bank_file.get_pattern(1)

        pattern.set_pitch(track=1, step=1, value=64)
        assert pattern.get_pitch(track=1, step=1) == 64

    def test_pattern_set_trig_condition(self, bank_file):
        """Test Pattern.set_trig_condition convenience method."""
        pattern = bank_file.get_pattern(1)

        pattern.set_trig_condition(track=1, step=1, condition=TrigCondition.FILL)
        assert pattern.get_trig_condition(track=1, step=1) == TrigCondition.FILL

    def test_pattern_set_trig_repeat(self, bank_file):
        """Test Pattern.set_trig_repeat convenience method."""
        pattern = bank_file.get_pattern(1)

        pattern.set_trig_repeat(track=1, step=1, count=4)
        assert pattern.get_trig_repeat(track=1, step=1) == 4


class TestPlockRoundTrip:
    """P-lock round-trip (save/load) tests."""

    def test_volume_plock_survives_save(self, bank_file, temp_dir):
        """Test that volume p-locks survive bank save/load."""
        bank_file.set_trigs(pattern=1, track=1, steps=[1, 5, 9, 13])

        # Set volume p-locks
        pattern = bank_file.get_pattern(1)
        pattern.set_volume(track=1, step=1, value=100)
        pattern.set_volume(track=1, step=5, value=75)
        pattern.set_volume(track=1, step=9, value=50)
        bank_file._patterns[0] = pattern

        # Save and reload
        path = temp_dir / "bank01.work"
        bank_file.to_file(path)
        loaded = BankFile.from_file(path)

        # Verify
        loaded_pattern = loaded.get_pattern(1)
        assert loaded_pattern.get_volume(track=1, step=1) == 100
        assert loaded_pattern.get_volume(track=1, step=5) == 75
        assert loaded_pattern.get_volume(track=1, step=9) == 50

    def test_pitch_plock_survives_save(self, bank_file, temp_dir):
        """Test that pitch p-locks survive bank save/load."""
        pattern = bank_file.get_pattern(1)
        pattern.set_pitch(track=1, step=1, value=64)
        pattern.set_pitch(track=1, step=2, value=72)
        bank_file._patterns[0] = pattern

        # Save and reload
        path = temp_dir / "bank01.work"
        bank_file.to_file(path)
        loaded = BankFile.from_file(path)

        # Verify
        loaded_pattern = loaded.get_pattern(1)
        assert loaded_pattern.get_pitch(track=1, step=1) == 64
        assert loaded_pattern.get_pitch(track=1, step=2) == 72

    def test_trig_condition_survives_save(self, bank_file, temp_dir):
        """Test that trig conditions survive bank save/load."""
        pattern = bank_file.get_pattern(1)
        pattern.set_trig_condition(track=1, step=1, condition=TrigCondition.FILL)
        pattern.set_trig_condition(track=1, step=5, condition=TrigCondition.PERCENT_50)
        bank_file._patterns[0] = pattern

        # Save and reload
        path = temp_dir / "bank01.work"
        bank_file.to_file(path)
        loaded = BankFile.from_file(path)

        # Verify
        loaded_pattern = loaded.get_pattern(1)
        assert loaded_pattern.get_trig_condition(track=1, step=1) == TrigCondition.FILL
        assert loaded_pattern.get_trig_condition(track=1, step=5) == TrigCondition.PERCENT_50


class TestTrigConditionEnum:
    """TrigCondition enum tests."""

    def test_none_is_zero(self):
        """Test that NONE has value 0."""
        assert TrigCondition.NONE == 0

    def test_fill_is_one(self):
        """Test that FILL has value 1."""
        assert TrigCondition.FILL == 1

    def test_probability_values(self):
        """Test probability condition values."""
        assert TrigCondition.PERCENT_50 == 19
        assert TrigCondition.PERCENT_75 == 22
        assert TrigCondition.PERCENT_25 == 16

    def test_pattern_loop_values(self):
        """Test pattern loop condition values."""
        assert TrigCondition.T1_R8 == 57
        assert TrigCondition.T8_R8 == 64


class TestPlockOffset:
    """PlockOffset enum tests."""

    def test_src_params(self):
        """Test SRC page param offsets."""
        assert PlockOffset.SRC_1 == 0
        assert PlockOffset.SRC_6 == 5

    def test_lfo_params(self):
        """Test LFO page param offsets."""
        assert PlockOffset.LFO_SPEED1 == 6
        assert PlockOffset.LFO_DEPTH3 == 11

    def test_amp_params(self):
        """Test AMP page param offsets."""
        assert PlockOffset.AMP_ATTACK == 12
        assert PlockOffset.AMP_VOLUME == 15
        assert PlockOffset.AMP_F == 17

    def test_fx_params(self):
        """Test FX page param offsets."""
        assert PlockOffset.FX1_1 == 18
        assert PlockOffset.FX1_6 == 23
        assert PlockOffset.FX2_1 == 24
        assert PlockOffset.FX2_6 == 29

    def test_slot_offsets(self):
        """Test sample slot offsets."""
        assert PlockOffset.STATIC_SLOT == 30
        assert PlockOffset.FLEX_SLOT == 31


class TestFlexMachinePlocks:
    """Tests for Flex/Static machine SRC page p-locks."""

    def test_flex_start(self, bank_file):
        """Test sample start p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_flex_start(step=1, value=64)
        assert track.get_flex_start(1) == 64

    def test_flex_length(self, bank_file):
        """Test sample length p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_flex_length(step=1, value=100)
        assert track.get_flex_length(1) == 100

    def test_flex_rate(self, bank_file):
        """Test playback rate p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        # Normal forward
        track.set_flex_rate(step=1, value=127)
        assert track.get_flex_rate(1) == 127

        # Reverse
        track.set_flex_rate(step=2, value=0)
        assert track.get_flex_rate(2) == 0

    def test_flex_retrig(self, bank_file):
        """Test retrig count p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_flex_retrig(step=1, value=4)
        assert track.get_flex_retrig(1) == 4

    def test_flex_retrig_time(self, bank_file):
        """Test retrig time p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_flex_retrig_time(step=1, value=79)
        assert track.get_flex_retrig_time(1) == 79


class TestThruMachinePlocks:
    """Tests for Thru machine SRC page p-locks."""

    def test_thru_in_ab(self, bank_file):
        """Test input A/B select p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_thru_in_ab(step=1, value=1)
        assert track.get_thru_in_ab(1) == 1

    def test_thru_vol_ab(self, bank_file):
        """Test volume A/B p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_thru_vol_ab(step=1, value=64)
        assert track.get_thru_vol_ab(1) == 64

    def test_thru_in_cd(self, bank_file):
        """Test input C/D select p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_thru_in_cd(step=1, value=1)
        assert track.get_thru_in_cd(1) == 1

    def test_thru_vol_cd(self, bank_file):
        """Test volume C/D p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_thru_vol_cd(step=1, value=64)
        assert track.get_thru_vol_cd(1) == 64


class TestPickupMachinePlocks:
    """Tests for Pickup machine SRC page p-locks."""

    def test_pickup_pitch(self, bank_file):
        """Test pitch p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_pickup_pitch(step=1, value=64)
        assert track.get_pickup_pitch(1) == 64

    def test_pickup_dir(self, bank_file):
        """Test direction p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_pickup_dir(step=1, value=2)
        assert track.get_pickup_dir(1) == 2

    def test_pickup_length(self, bank_file):
        """Test length p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_pickup_length(step=1, value=1)
        assert track.get_pickup_length(1) == 1

    def test_pickup_gain(self, bank_file):
        """Test gain p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_pickup_gain(step=1, value=64)
        assert track.get_pickup_gain(1) == 64

    def test_pickup_op(self, bank_file):
        """Test operation mode p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_pickup_op(step=1, value=1)
        assert track.get_pickup_op(1) == 1


class TestLfoPlocks:
    """Tests for LFO page p-locks."""

    def test_lfo_speeds(self, bank_file):
        """Test LFO speed p-locks."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_lfo_speed1(step=1, value=32)
        track.set_lfo_speed2(step=1, value=64)
        track.set_lfo_speed3(step=1, value=96)

        assert track.get_lfo_speed1(1) == 32
        assert track.get_lfo_speed2(1) == 64
        assert track.get_lfo_speed3(1) == 96

    def test_lfo_depths(self, bank_file):
        """Test LFO depth p-locks."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_lfo_depth1(step=1, value=50)
        track.set_lfo_depth2(step=1, value=75)
        track.set_lfo_depth3(step=1, value=100)

        assert track.get_lfo_depth1(1) == 50
        assert track.get_lfo_depth2(1) == 75
        assert track.get_lfo_depth3(1) == 100


class TestAmpPlocks:
    """Tests for AMP page p-locks."""

    def test_amp_envelope(self, bank_file):
        """Test attack/hold/release p-locks."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_amp_attack(step=1, value=10)
        track.set_amp_hold(step=1, value=64)
        track.set_amp_release(step=1, value=100)

        assert track.get_amp_attack(1) == 10
        assert track.get_amp_hold(1) == 64
        assert track.get_amp_release(1) == 100

    def test_amp_balance(self, bank_file):
        """Test balance p-lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_amp_balance(step=1, value=32)
        assert track.get_amp_balance(1) == 32


class TestFxPlocks:
    """Tests for FX page p-locks."""

    def test_fx1_params(self, bank_file):
        """Test FX1 param p-locks."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        for i, setter in enumerate([
            track.set_fx1_1, track.set_fx1_2, track.set_fx1_3,
            track.set_fx1_4, track.set_fx1_5, track.set_fx1_6
        ], 1):
            setter(step=1, value=i * 10)

        assert track.get_fx1_1(1) == 10
        assert track.get_fx1_2(1) == 20
        assert track.get_fx1_3(1) == 30
        assert track.get_fx1_4(1) == 40
        assert track.get_fx1_5(1) == 50
        assert track.get_fx1_6(1) == 60

    def test_fx2_params(self, bank_file):
        """Test FX2 param p-locks."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_fx2_1(step=1, value=100)
        track.set_fx2_6(step=1, value=50)

        assert track.get_fx2_1(1) == 100
        assert track.get_fx2_6(1) == 50


class TestSampleSlotLocks:
    """Tests for sample slot lock p-locks."""

    def test_static_slot_lock(self, bank_file):
        """Test static sample slot lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_static_slot_lock(step=1, value=5)
        assert track.get_static_slot_lock(1) == 5

    def test_flex_slot_lock(self, bank_file):
        """Test flex sample slot lock."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_flex_slot_lock(step=1, value=10)
        assert track.get_flex_slot_lock(1) == 10


class TestExtendedSteps:
    """Tests for extended pattern steps (17-64)."""

    def test_volume_plock_on_extended_steps(self, bank_file):
        """Test volume p-locks on steps 17-64."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        # Set volume on various extended steps
        track.set_volume(step=17, value=100)
        track.set_volume(step=33, value=75)
        track.set_volume(step=64, value=50)

        assert track.get_volume(17) == 100
        assert track.get_volume(33) == 75
        assert track.get_volume(64) == 50

    def test_trig_condition_on_extended_steps(self, bank_file):
        """Test trig conditions on steps 17-64."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        track.set_trig_condition(step=32, condition=TrigCondition.FILL)
        track.set_trig_condition(step=48, condition=TrigCondition.PERCENT_50)
        track.set_trig_condition(step=64, condition=TrigCondition.T1_R4)

        assert track.get_trig_condition(32) == TrigCondition.FILL
        assert track.get_trig_condition(48) == TrigCondition.PERCENT_50
        assert track.get_trig_condition(64) == TrigCondition.T1_R4

    def test_invalid_step_raises(self, bank_file):
        """Test that invalid step numbers raise ValueError."""
        pattern = bank_file.get_pattern(1)
        track = pattern.get_audio_track(1)

        with pytest.raises(ValueError):
            track.get_volume(0)

        with pytest.raises(ValueError):
            track.get_volume(65)

        with pytest.raises(ValueError):
            track.set_volume(step=0, value=100)
