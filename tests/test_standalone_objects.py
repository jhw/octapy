"""
Tests for standalone objects (Phase 1 of standalone object migration).
"""

import pytest
from octapy import RecorderSetup, RecordingSource, RecTrigMode, QRecMode, TrigCondition
from octapy._io import RECORDER_SETUP_SIZE, OCTAPY_DEFAULT_RECORDER_SETUP, PLOCK_SIZE
from octapy.api.objects import AudioStep


class TestRecorderSetupStandalone:
    """Tests for standalone RecorderSetup object."""

    def test_default_construction(self):
        """RecorderSetup() creates object with octapy defaults."""
        recorder = RecorderSetup()

        # Check octapy defaults
        assert recorder.source == RecordingSource.OFF
        assert recorder.rlen == 15  # displays as 16
        assert recorder.trig == RecTrigMode.ONE
        assert recorder.loop == False
        assert recorder.qrec == QRecMode.PLEN
        assert recorder.qpl == 255  # OFF

    def test_constructor_with_kwargs(self):
        """RecorderSetup accepts kwargs for all properties."""
        recorder = RecorderSetup(
            source=RecordingSource.TRACK_3,
            rlen=32,
            trig=RecTrigMode.HOLD,
            loop=True,
            fin=16,
            fout=8,
            ab_gain=64,
            qrec=QRecMode.OFF,
            qpl=0,
            cd_gain=48,
        )

        assert recorder.source == RecordingSource.TRACK_3
        assert recorder.rlen == 32
        assert recorder.trig == RecTrigMode.HOLD
        assert recorder.loop == True
        assert recorder.fin == 16
        assert recorder.fout == 8
        assert recorder.ab_gain == 64
        assert recorder.qrec == QRecMode.OFF
        assert recorder.qpl == 0
        assert recorder.cd_gain == 48

    def test_partial_kwargs(self):
        """RecorderSetup with partial kwargs uses defaults for others."""
        recorder = RecorderSetup(source=RecordingSource.INPUT_AB, rlen=8)

        assert recorder.source == RecordingSource.INPUT_AB
        assert recorder.rlen == 8
        # Rest should be defaults
        assert recorder.trig == RecTrigMode.ONE
        assert recorder.loop == False
        assert recorder.qrec == QRecMode.PLEN

    def test_write_produces_correct_size(self):
        """write() returns RECORDER_SETUP_SIZE bytes."""
        recorder = RecorderSetup()
        data = recorder.write()

        assert len(data) == RECORDER_SETUP_SIZE
        assert isinstance(data, bytes)

    def test_write_produces_default_bytes(self):
        """write() on default object matches OCTAPY_DEFAULT_RECORDER_SETUP."""
        recorder = RecorderSetup()
        data = recorder.write()

        assert data == OCTAPY_DEFAULT_RECORDER_SETUP

    def test_read_creates_equivalent_object(self):
        """read() from written data creates equivalent object."""
        original = RecorderSetup(
            source=RecordingSource.TRACK_5,
            rlen=24,
            trig=RecTrigMode.ONE2,
            loop=True,
        )

        data = original.write()
        restored = RecorderSetup.read(data)

        assert restored.source == original.source
        assert restored.rlen == original.rlen
        assert restored.trig == original.trig
        assert restored.loop == original.loop

    def test_round_trip(self):
        """read(write(x)) produces equivalent object."""
        original = RecorderSetup(
            source=RecordingSource.MAIN,
            rlen=64,  # MAX
            trig=RecTrigMode.HOLD,
            loop=False,
            fin=32,
            fout=16,
            ab_gain=100,
            qrec=QRecMode.PLEN,
            qpl=64,
            cd_gain=50,
        )

        data = original.write()
        restored = RecorderSetup.read(data)

        # All properties should match
        assert restored.source == original.source
        assert restored.rlen == original.rlen
        assert restored.trig == original.trig
        assert restored.loop == original.loop
        assert restored.fin == original.fin
        assert restored.fout == original.fout
        assert restored.ab_gain == original.ab_gain
        assert restored.qrec == original.qrec
        assert restored.qpl == original.qpl
        assert restored.cd_gain == original.cd_gain

        # Data should be byte-for-byte equal
        assert restored._data == original._data

    def test_clone(self):
        """clone() creates independent copy."""
        original = RecorderSetup(source=RecordingSource.TRACK_1, rlen=16)
        cloned = original.clone()

        # Should be equal
        assert cloned.source == original.source
        assert cloned.rlen == original.rlen

        # But independent - modifying clone doesn't affect original
        cloned.source = RecordingSource.TRACK_2
        cloned.rlen = 32

        assert original.source == RecordingSource.TRACK_1
        assert original.rlen == 16

    def test_equality(self):
        """RecorderSetup objects with same data are equal."""
        a = RecorderSetup(source=RecordingSource.TRACK_1, rlen=16)
        b = RecorderSetup(source=RecordingSource.TRACK_1, rlen=16)
        c = RecorderSetup(source=RecordingSource.TRACK_2, rlen=16)

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns all properties."""
        recorder = RecorderSetup(
            source=RecordingSource.TRACK_3,
            rlen=16,
            trig=RecTrigMode.ONE,
            loop=False,
        )

        d = recorder.to_dict()

        assert d["source"] == "TRACK_3"
        assert d["rlen"] == 16
        assert d["trig"] == "ONE"
        assert d["loop"] == False

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = RecorderSetup(
            source=RecordingSource.INPUT_AB,
            rlen=24,
            trig=RecTrigMode.HOLD,
            loop=True,
        )

        d = original.to_dict()
        restored = RecorderSetup.from_dict(d)

        assert restored.source == original.source
        assert restored.rlen == original.rlen
        assert restored.trig == original.trig
        assert restored.loop == original.loop

    def test_from_dict_with_enum_names(self):
        """from_dict() handles enum names as strings."""
        d = {
            "source": "TRACK_1",
            "rlen": 16,
            "trig": "ONE2",
            "loop": False,
            "qrec": "OFF",
        }

        recorder = RecorderSetup.from_dict(d)

        assert recorder.source == RecordingSource.TRACK_1
        assert recorder.rlen == 16
        assert recorder.trig == RecTrigMode.ONE2
        assert recorder.qrec == QRecMode.OFF


class TestRecorderSetupSources:
    """Tests for RecorderSetup source property."""

    def test_track_sources(self):
        """Source property handles TRACK_1 through TRACK_8."""
        for track_num in range(1, 9):
            source = RecordingSource[f"TRACK_{track_num}"]
            recorder = RecorderSetup(source=source)

            assert recorder.source == source

            # Round-trip through write/read
            restored = RecorderSetup.read(recorder.write())
            assert restored.source == source

    def test_input_sources(self):
        """Source property handles external input sources."""
        for source in [
            RecordingSource.INPUT_AB,
            RecordingSource.INPUT_A,
            RecordingSource.INPUT_B,
            RecordingSource.INPUT_CD,
            RecordingSource.INPUT_C,
            RecordingSource.INPUT_D,
        ]:
            recorder = RecorderSetup(source=source)
            assert recorder.source == source

            # Round-trip
            restored = RecorderSetup.read(recorder.write())
            assert restored.source == source

    def test_main_source(self):
        """Source property handles MAIN source."""
        recorder = RecorderSetup(source=RecordingSource.MAIN)

        assert recorder.source == RecordingSource.MAIN

        # Round-trip
        restored = RecorderSetup.read(recorder.write())
        assert restored.source == RecordingSource.MAIN

    def test_off_source(self):
        """Source property handles OFF (no source)."""
        recorder = RecorderSetup(source=RecordingSource.OFF)

        assert recorder.source == RecordingSource.OFF

        # Round-trip
        restored = RecorderSetup.read(recorder.write())
        assert restored.source == RecordingSource.OFF


class TestRecorderSetupRepr:
    """Tests for RecorderSetup string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        recorder = RecorderSetup(
            source=RecordingSource.TRACK_1,
            rlen=16,
            trig=RecTrigMode.ONE,
        )

        r = repr(recorder)
        assert "RecorderSetup" in r
        assert "TRACK_1" in r
        assert "rlen=16" in r
        assert "ONE" in r


# =============================================================================
# AudioStep Tests
# =============================================================================

class TestAudioStepStandalone:
    """Tests for standalone AudioStep object."""

    def test_default_construction(self):
        """AudioStep() creates object with defaults."""
        step = AudioStep()

        assert step.step_num == 1
        assert step.active == False
        assert step.trigless == False
        assert step.condition == TrigCondition.NONE
        assert step.volume is None
        assert step.pitch is None

    def test_constructor_with_kwargs(self):
        """AudioStep accepts kwargs for all properties."""
        step = AudioStep(
            step_num=5,
            active=True,
            trigless=False,
            condition=TrigCondition.FILL,
            volume=100,
            pitch=72,
            sample_lock=3,
        )

        assert step.step_num == 5
        assert step.active == True
        assert step.trigless == False
        assert step.condition == TrigCondition.FILL
        assert step.volume == 100
        assert step.pitch == 72
        assert step.sample_lock == 3

    def test_probability_kwarg(self):
        """AudioStep accepts probability kwarg."""
        step = AudioStep(step_num=1, active=True, probability=0.5)

        # Should set a probability condition
        assert step.probability is not None
        assert 0.45 <= step.probability <= 0.55  # Allow some rounding

    def test_partial_kwargs(self):
        """AudioStep with partial kwargs uses defaults for others."""
        step = AudioStep(step_num=3, active=True, volume=80)

        assert step.step_num == 3
        assert step.active == True
        assert step.trigless == False
        assert step.condition == TrigCondition.NONE
        assert step.volume == 80
        assert step.pitch is None

    def test_write_returns_components(self):
        """write() returns (active, trigless, condition_data, plock_data)."""
        step = AudioStep(step_num=1, active=True, trigless=False)
        active, trigless, condition_data, plock_data = step.write()

        assert active == True
        assert trigless == False
        assert len(condition_data) == 2
        assert len(plock_data) == PLOCK_SIZE

    def test_read_creates_equivalent_object(self):
        """read() from written data creates equivalent object."""
        original = AudioStep(
            step_num=5,
            active=True,
            condition=TrigCondition.FILL,
            volume=100,
        )

        active, trigless, condition_data, plock_data = original.write()
        restored = AudioStep.read(5, active, trigless, condition_data, plock_data)

        assert restored.step_num == original.step_num
        assert restored.active == original.active
        assert restored.trigless == original.trigless
        assert restored.condition == original.condition
        assert restored.volume == original.volume

    def test_round_trip(self):
        """read(write(x)) produces equivalent object."""
        original = AudioStep(
            step_num=9,
            active=True,
            trigless=True,
            condition=TrigCondition.PRE,
            volume=64,
            pitch=70,
            sample_lock=5,
        )

        active, trigless, condition_data, plock_data = original.write()
        restored = AudioStep.read(9, active, trigless, condition_data, plock_data)

        # All properties should match
        assert restored.step_num == original.step_num
        assert restored.active == original.active
        assert restored.trigless == original.trigless
        assert restored.condition == original.condition
        assert restored.volume == original.volume
        assert restored.pitch == original.pitch
        assert restored.sample_lock == original.sample_lock

    def test_clone(self):
        """clone() creates independent copy."""
        original = AudioStep(step_num=1, active=True, volume=100)
        cloned = original.clone()

        # Should be equal
        assert cloned.step_num == original.step_num
        assert cloned.active == original.active
        assert cloned.volume == original.volume

        # But independent - modifying clone doesn't affect original
        cloned.active = False
        cloned.volume = 50

        assert original.active == True
        assert original.volume == 100

    def test_equality(self):
        """AudioStep objects with same data are equal."""
        a = AudioStep(step_num=1, active=True, volume=100)
        b = AudioStep(step_num=1, active=True, volume=100)
        c = AudioStep(step_num=1, active=True, volume=80)

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns step properties."""
        step = AudioStep(
            step_num=5,
            active=True,
            condition=TrigCondition.FILL,
            volume=100,
        )

        d = step.to_dict()

        assert d["step"] == 5
        assert d["active"] == True
        assert d["trigless"] == False
        assert d["condition"] == "FILL"
        assert d["volume"] == 100

    def test_to_dict_minimal(self):
        """to_dict() omits unset values."""
        step = AudioStep(step_num=1, active=False)

        d = step.to_dict()

        assert d["step"] == 1
        assert d["active"] == False
        assert "condition" not in d  # NONE is omitted
        assert "volume" not in d  # None p-locks omitted

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = AudioStep(
            step_num=5,
            active=True,
            condition=TrigCondition.FILL,
            volume=100,
        )

        d = original.to_dict()
        restored = AudioStep.from_dict(d)

        assert restored.step_num == original.step_num
        assert restored.active == original.active
        assert restored.condition == original.condition
        assert restored.volume == original.volume


class TestAudioStepConditions:
    """Tests for AudioStep condition handling."""

    def test_condition_none(self):
        """Default condition is NONE."""
        step = AudioStep()
        assert step.condition == TrigCondition.NONE

    def test_condition_fill(self):
        """FILL condition works."""
        step = AudioStep(condition=TrigCondition.FILL)
        assert step.condition == TrigCondition.FILL

    def test_condition_pre(self):
        """PRE condition works."""
        step = AudioStep(condition=TrigCondition.PRE)
        assert step.condition == TrigCondition.PRE

    def test_probability_setter(self):
        """Setting probability sets appropriate condition."""
        step = AudioStep()
        step.probability = 0.5

        # Should have set a condition with ~50% probability
        assert step.probability is not None

    def test_probability_clear(self):
        """Setting probability to None or 1.0 clears condition."""
        step = AudioStep(probability=0.5)
        assert step.probability is not None

        step.probability = None
        assert step.condition == TrigCondition.NONE


class TestAudioStepRepr:
    """Tests for AudioStep string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        step = AudioStep(step_num=5, active=True)

        r = repr(step)
        assert "AudioStep" in r
        assert "step=5" in r
        assert "active=True" in r
