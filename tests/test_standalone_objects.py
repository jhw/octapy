"""
Tests for standalone objects (Phase 1 of standalone object migration).
"""

import pytest
from octapy import RecorderSetup, RecordingSource, RecTrigMode, QRecMode, TrigCondition, MachineType, FX1Type, FX2Type
from octapy._io import RECORDER_SETUP_SIZE, OCTAPY_DEFAULT_RECORDER_SETUP, PLOCK_SIZE, MIDI_PLOCK_SIZE, AUDIO_TRACK_SIZE, MIDI_TRACK_PATTERN_SIZE
from octapy.api.objects import AudioStep, MidiStep, AudioPartTrack, AudioPatternTrack, MidiPartTrack, MidiPatternTrack
from octapy.api.objects.midi_part_track import MIDI_PART_TRACK_SIZE


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


# =============================================================================
# MidiStep Tests
# =============================================================================

class TestMidiStepStandalone:
    """Tests for standalone MidiStep object."""

    def test_default_construction(self):
        """MidiStep() creates object with defaults."""
        step = MidiStep()

        assert step.step_num == 1
        assert step.active == False
        assert step.trigless == False
        assert step.condition == TrigCondition.NONE
        assert step.note is None
        assert step.velocity is None
        assert step.length is None

    def test_constructor_with_kwargs(self):
        """MidiStep accepts kwargs for all MIDI properties."""
        step = MidiStep(
            step_num=5,
            active=True,
            trigless=False,
            condition=TrigCondition.FILL,
            note=60,
            velocity=100,
            length=6,
            pitch_bend=64,
            aftertouch=50,
        )

        assert step.step_num == 5
        assert step.active == True
        assert step.trigless == False
        assert step.condition == TrigCondition.FILL
        assert step.note == 60
        assert step.velocity == 100
        assert step.length == 6
        assert step.pitch_bend == 64
        assert step.aftertouch == 50

    def test_partial_kwargs(self):
        """MidiStep with partial kwargs uses defaults for others."""
        step = MidiStep(step_num=3, active=True, note=72)

        assert step.step_num == 3
        assert step.active == True
        assert step.note == 72
        assert step.velocity is None
        assert step.length is None

    def test_write_returns_components(self):
        """write() returns (active, trigless, condition_data, plock_data)."""
        step = MidiStep(step_num=1, active=True)
        active, trigless, condition_data, plock_data = step.write()

        assert active == True
        assert trigless == False
        assert len(condition_data) == 2
        assert len(plock_data) == MIDI_PLOCK_SIZE

    def test_read_creates_equivalent_object(self):
        """read() from written data creates equivalent object."""
        original = MidiStep(
            step_num=5,
            active=True,
            note=60,
            velocity=100,
        )

        active, trigless, condition_data, plock_data = original.write()
        restored = MidiStep.read(5, active, trigless, condition_data, plock_data)

        assert restored.step_num == original.step_num
        assert restored.active == original.active
        assert restored.note == original.note
        assert restored.velocity == original.velocity

    def test_round_trip(self):
        """read(write(x)) produces equivalent object."""
        original = MidiStep(
            step_num=9,
            active=True,
            trigless=True,
            condition=TrigCondition.PRE,
            note=48,
            velocity=80,
            length=12,
            pitch_bend=70,
            aftertouch=30,
        )

        active, trigless, condition_data, plock_data = original.write()
        restored = MidiStep.read(9, active, trigless, condition_data, plock_data)

        assert restored.step_num == original.step_num
        assert restored.active == original.active
        assert restored.trigless == original.trigless
        assert restored.condition == original.condition
        assert restored.note == original.note
        assert restored.velocity == original.velocity
        assert restored.length == original.length
        assert restored.pitch_bend == original.pitch_bend
        assert restored.aftertouch == original.aftertouch

    def test_clone(self):
        """clone() creates independent copy."""
        original = MidiStep(step_num=1, active=True, note=60)
        cloned = original.clone()

        # Should be equal
        assert cloned.step_num == original.step_num
        assert cloned.note == original.note

        # But independent
        cloned.note = 72
        assert original.note == 60

    def test_equality(self):
        """MidiStep objects with same data are equal."""
        a = MidiStep(step_num=1, active=True, note=60)
        b = MidiStep(step_num=1, active=True, note=60)
        c = MidiStep(step_num=1, active=True, note=72)

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns MIDI step properties."""
        step = MidiStep(
            step_num=5,
            active=True,
            note=60,
            velocity=100,
        )

        d = step.to_dict()

        assert d["step"] == 5
        assert d["active"] == True
        assert d["note"] == 60
        assert d["velocity"] == 100

    def test_to_dict_minimal(self):
        """to_dict() omits unset values."""
        step = MidiStep(step_num=1, active=False)

        d = step.to_dict()

        assert d["step"] == 1
        assert d["active"] == False
        assert "note" not in d
        assert "velocity" not in d

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = MidiStep(
            step_num=5,
            active=True,
            note=60,
            velocity=100,
        )

        d = original.to_dict()
        restored = MidiStep.from_dict(d)

        assert restored.step_num == original.step_num
        assert restored.active == original.active
        assert restored.note == original.note
        assert restored.velocity == original.velocity


class TestMidiStepCC:
    """Tests for MidiStep CC handling."""

    def test_cc_get_set(self):
        """CC values can be get/set by slot number."""
        step = MidiStep()

        step.set_cc(1, 64)
        step.set_cc(5, 127)

        assert step.cc(1) == 64
        assert step.cc(5) == 127
        assert step.cc(2) is None

    def test_cc_invalid_slot(self):
        """Invalid CC slot raises ValueError."""
        step = MidiStep()

        with pytest.raises(ValueError):
            step.cc(0)

        with pytest.raises(ValueError):
            step.cc(11)

        with pytest.raises(ValueError):
            step.set_cc(0, 64)

    def test_cc_in_to_dict(self):
        """CC values are included in to_dict."""
        step = MidiStep(active=True)
        step.set_cc(1, 64)
        step.set_cc(3, 100)

        d = step.to_dict()

        assert "cc" in d
        assert d["cc"][1] == 64
        assert d["cc"][3] == 100

    def test_cc_from_dict(self):
        """CC values are restored from dict."""
        step = MidiStep(active=True)
        step.set_cc(1, 64)
        step.set_cc(3, 100)

        d = step.to_dict()
        restored = MidiStep.from_dict(d)

        assert restored.cc(1) == 64
        assert restored.cc(3) == 100


class TestMidiStepRepr:
    """Tests for MidiStep string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        step = MidiStep(step_num=5, active=True)

        r = repr(step)
        assert "MidiStep" in r
        assert "step=5" in r
        assert "active=True" in r


# =============================================================================
# AudioPartTrack Tests (Phase 2)
# =============================================================================

class TestAudioPartTrackStandalone:
    """Tests for standalone AudioPartTrack object."""

    def test_default_construction(self):
        """AudioPartTrack() creates object with defaults."""
        track = AudioPartTrack()

        assert track.track_num == 1
        assert track.machine_type == MachineType.FLEX
        assert track.flex_slot == 0
        assert track.static_slot == 0
        assert track.recorder_slot == 0
        assert track.volume == (108, 108)
        assert track.attack == 0
        assert track.hold == 127
        assert track.release == 24
        assert track.amp_volume == 108
        assert track.balance == 64

    def test_constructor_with_kwargs(self):
        """AudioPartTrack accepts kwargs for all properties."""
        track = AudioPartTrack(
            track_num=3,
            machine_type=MachineType.STATIC,
            flex_slot=5,
            static_slot=10,
            recorder_slot=2,
            main_volume=100,
            cue_volume=90,
            fx1_type=FX1Type.EQ,
            fx2_type=FX2Type.PLATE_REVERB,
            attack=10,
            hold=100,
            release=50,
            amp_volume=80,
            balance=70,
        )

        assert track.track_num == 3
        assert track.machine_type == MachineType.STATIC
        assert track.flex_slot == 5
        assert track.static_slot == 10
        assert track.recorder_slot == 2
        assert track.volume == (100, 90)
        assert track.fx1_type == FX1Type.EQ
        assert track.fx2_type == FX2Type.PLATE_REVERB
        assert track.attack == 10
        assert track.hold == 100
        assert track.release == 50
        assert track.amp_volume == 80
        assert track.balance == 70

    def test_partial_kwargs(self):
        """AudioPartTrack with partial kwargs uses defaults for others."""
        track = AudioPartTrack(
            track_num=2,
            machine_type=MachineType.FLEX,
            flex_slot=3,
        )

        assert track.track_num == 2
        assert track.machine_type == MachineType.FLEX
        assert track.flex_slot == 3
        # Other defaults
        assert track.static_slot == 0
        assert track.volume == (108, 108)

    def test_recorder_property(self):
        """AudioPartTrack has embedded RecorderSetup."""
        track = AudioPartTrack()

        recorder = track.recorder
        assert isinstance(recorder, RecorderSetup)

        # Modify recorder
        recorder.source = RecordingSource.TRACK_3
        recorder.rlen = 32

        assert track.recorder.source == RecordingSource.TRACK_3
        assert track.recorder.rlen == 32

    def test_recorder_in_constructor(self):
        """AudioPartTrack accepts RecorderSetup in constructor."""
        recorder = RecorderSetup(
            source=RecordingSource.INPUT_AB,
            rlen=16,
        )
        track = AudioPartTrack(recorder=recorder)

        assert track.recorder.source == RecordingSource.INPUT_AB
        assert track.recorder.rlen == 16

    def test_clone(self):
        """clone() creates independent copy."""
        original = AudioPartTrack(
            track_num=1,
            machine_type=MachineType.FLEX,
            flex_slot=5,
        )
        original.recorder.source = RecordingSource.TRACK_2

        cloned = original.clone()

        # Should be equal
        assert cloned.track_num == original.track_num
        assert cloned.machine_type == original.machine_type
        assert cloned.flex_slot == original.flex_slot
        assert cloned.recorder.source == original.recorder.source

        # But independent
        cloned.flex_slot = 10
        cloned.recorder.source = RecordingSource.TRACK_5

        assert original.flex_slot == 5
        assert original.recorder.source == RecordingSource.TRACK_2

    def test_equality(self):
        """AudioPartTrack objects with same data are equal."""
        a = AudioPartTrack(track_num=1, machine_type=MachineType.FLEX, flex_slot=5)
        b = AudioPartTrack(track_num=1, machine_type=MachineType.FLEX, flex_slot=5)
        c = AudioPartTrack(track_num=1, machine_type=MachineType.STATIC, flex_slot=5)

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns track properties."""
        track = AudioPartTrack(
            track_num=1,
            machine_type=MachineType.FLEX,
            flex_slot=5,
            fx1_type=FX1Type.FILTER,
        )

        d = track.to_dict()

        assert d["track"] == 1
        assert d["machine_type"] == "FLEX"
        assert d["flex_slot"] == 5
        assert d["fx1_type"] == FX1Type.FILTER
        assert "recorder" in d
        assert "volume" in d
        assert "amp" in d

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = AudioPartTrack(
            track_num=2,
            machine_type=MachineType.STATIC,
            static_slot=10,
            fx1_type=FX1Type.EQ,
        )
        original.recorder.source = RecordingSource.TRACK_1

        d = original.to_dict()
        restored = AudioPartTrack.from_dict(d)

        assert restored.track_num == original.track_num
        assert restored.machine_type == original.machine_type
        assert restored.static_slot == original.static_slot
        assert restored.fx1_type == original.fx1_type
        assert restored.recorder.source == original.recorder.source

    def test_fx_type_applies_defaults(self):
        """Setting FX type applies per-type default parameters."""
        track = AudioPartTrack()

        # Setting FX1 type should apply defaults
        track.fx1_type = FX1Type.CHORUS
        # The defaults are applied internally - just verify no error

        track.fx2_type = FX2Type.DARK_REVERB
        # Again, just verify no error


class TestAudioPartTrackSRCPage:
    """Tests for AudioPartTrack SRC/Playback page properties."""

    def test_pitch_property(self):
        """pitch property works."""
        track = AudioPartTrack()
        track.pitch = 72

        assert track.pitch == 72

    def test_start_property(self):
        """start property works."""
        track = AudioPartTrack()
        track.start = 32

        assert track.start == 32

    def test_length_property(self):
        """length property works."""
        track = AudioPartTrack()
        track.length = 64

        assert track.length == 64

    def test_rate_property(self):
        """rate property works."""
        track = AudioPartTrack()
        track.rate = 100

        assert track.rate == 100


class TestAudioPartTrackRepr:
    """Tests for AudioPartTrack string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        track = AudioPartTrack(track_num=3, machine_type=MachineType.STATIC)

        r = repr(track)
        assert "AudioPartTrack" in r
        assert "track=3" in r
        assert "STATIC" in r


# =============================================================================
# AudioPatternTrack Tests (Phase 2)
# =============================================================================

class TestAudioPatternTrackStandalone:
    """Tests for standalone AudioPatternTrack object."""

    def test_default_construction(self):
        """AudioPatternTrack() creates object with defaults."""
        track = AudioPatternTrack()

        assert track.track_num == 1
        assert track.active_steps == []
        assert track.trigless_steps == []

    def test_constructor_with_active_steps(self):
        """AudioPatternTrack accepts active_steps in constructor."""
        track = AudioPatternTrack(
            track_num=2,
            active_steps=[1, 5, 9, 13],
        )

        assert track.track_num == 2
        assert track.active_steps == [1, 5, 9, 13]

    def test_constructor_with_trigless_steps(self):
        """AudioPatternTrack accepts trigless_steps in constructor."""
        track = AudioPatternTrack(
            track_num=1,
            trigless_steps=[3, 7, 11, 15],
        )

        assert track.trigless_steps == [3, 7, 11, 15]

    def test_step_access(self):
        """step() returns AudioStep for given position."""
        track = AudioPatternTrack()

        step = track.step(5)
        assert isinstance(step, AudioStep)
        assert step.step_num == 5

    def test_step_modification(self):
        """Modifying a step affects the track."""
        track = AudioPatternTrack()

        step = track.step(5)
        step.active = True
        step.volume = 100

        # Step should retain modifications
        assert track.step(5).active == True
        assert track.step(5).volume == 100

    def test_active_steps_setter(self):
        """Setting active_steps updates the track."""
        track = AudioPatternTrack()

        track.active_steps = [1, 2, 3, 4]
        assert track.active_steps == [1, 2, 3, 4]

        # Verify steps are marked active
        assert track.step(1).active == True
        assert track.step(5).active == False

    def test_write_returns_correct_size(self):
        """write() returns AUDIO_TRACK_SIZE bytes."""
        track = AudioPatternTrack()
        data = track.write()

        assert len(data) == AUDIO_TRACK_SIZE
        assert isinstance(data, bytes)

    def test_read_write_round_trip(self):
        """read(write(x)) preserves data."""
        original = AudioPatternTrack(
            track_num=3,
            active_steps=[1, 5, 9, 13],
            trigless_steps=[2, 6],
        )
        original.step(5).volume = 100
        original.step(5).condition = TrigCondition.FILL

        data = original.write()
        restored = AudioPatternTrack.read(3, data)

        assert restored.track_num == original.track_num
        assert restored.active_steps == original.active_steps
        assert restored.trigless_steps == original.trigless_steps
        assert restored.step(5).volume == 100
        assert restored.step(5).condition == TrigCondition.FILL

    def test_clone(self):
        """clone() creates independent copy."""
        original = AudioPatternTrack(
            track_num=1,
            active_steps=[1, 5, 9],
        )

        cloned = original.clone()

        # Should have same data
        assert cloned.active_steps == original.active_steps

        # But be independent
        cloned.active_steps = [2, 6, 10]
        assert original.active_steps == [1, 5, 9]

    def test_equality(self):
        """AudioPatternTrack objects with same data are equal."""
        a = AudioPatternTrack(track_num=1, active_steps=[1, 5, 9])
        b = AudioPatternTrack(track_num=1, active_steps=[1, 5, 9])
        c = AudioPatternTrack(track_num=1, active_steps=[1, 5, 13])

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns track properties."""
        track = AudioPatternTrack(
            track_num=1,
            active_steps=[1, 5, 9, 13],
        )

        d = track.to_dict()

        assert d["track"] == 1
        assert d["active_steps"] == [1, 5, 9, 13]
        assert d["trigless_steps"] == []

    def test_to_dict_with_steps(self):
        """to_dict(include_steps=True) includes step data."""
        track = AudioPatternTrack(active_steps=[1, 5])
        track.step(1).volume = 100
        track.step(5).condition = TrigCondition.FILL

        d = track.to_dict(include_steps=True)

        assert "steps" in d
        assert len(d["steps"]) >= 2

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = AudioPatternTrack(
            track_num=2,
            active_steps=[1, 5, 9],
        )

        d = original.to_dict()
        restored = AudioPatternTrack.from_dict(d)

        assert restored.track_num == original.track_num
        assert restored.active_steps == original.active_steps


class TestAudioPatternTrackRepr:
    """Tests for AudioPatternTrack string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        track = AudioPatternTrack(track_num=2, active_steps=[1, 5, 9])

        r = repr(track)
        assert "AudioPatternTrack" in r
        assert "track=2" in r
        assert "active_steps=3" in r


# =============================================================================
# MidiPartTrack Tests (Phase 2)
# =============================================================================

class TestMidiPartTrackStandalone:
    """Tests for standalone MidiPartTrack object."""

    def test_default_construction(self):
        """MidiPartTrack() creates object with defaults."""
        track = MidiPartTrack()

        assert track.track_num == 1
        assert track.channel == 0  # Channel 1 (0-indexed)
        assert track.bank == 128  # Off
        assert track.program == 128  # Off
        assert track.default_note == 48  # C3
        assert track.default_velocity == 100
        assert track.default_length == 6  # 1/16
        assert track.default_note2 == 64  # No offset
        assert track.default_note3 == 64
        assert track.default_note4 == 64
        assert track.pitch_bend == 64  # Center
        assert track.aftertouch == 0

    def test_constructor_with_kwargs(self):
        """MidiPartTrack accepts kwargs for all properties."""
        track = MidiPartTrack(
            track_num=3,
            channel=5,
            bank=32,
            program=64,
            default_note=60,
            default_velocity=80,
            default_length=12,
            pitch_bend=70,
            aftertouch=50,
            arp_transpose=60,
            arp_mode=2,
        )

        assert track.track_num == 3
        assert track.channel == 5
        assert track.bank == 32
        assert track.program == 64
        assert track.default_note == 60
        assert track.default_velocity == 80
        assert track.default_length == 12
        assert track.pitch_bend == 70
        assert track.aftertouch == 50
        assert track.arp_transpose == 60
        assert track.arp_mode == 2

    def test_partial_kwargs(self):
        """MidiPartTrack with partial kwargs uses defaults for others."""
        track = MidiPartTrack(
            track_num=2,
            channel=10,
            default_note=72,
        )

        assert track.track_num == 2
        assert track.channel == 10
        assert track.default_note == 72
        # Other defaults
        assert track.bank == 128
        assert track.default_velocity == 100

    def test_cc_number_get_set(self):
        """CC number assignments can be get/set."""
        track = MidiPartTrack()

        track.set_cc_number(1, 74)  # CC74 (filter cutoff)
        track.set_cc_number(5, 71)  # CC71 (resonance)

        assert track.cc_number(1) == 74
        assert track.cc_number(5) == 71

    def test_cc_value_get_set(self):
        """CC default values can be get/set."""
        track = MidiPartTrack()

        track.set_cc_value(1, 64)
        track.set_cc_value(3, 100)

        assert track.cc_value(1) == 64
        assert track.cc_value(3) == 100

    def test_cc_invalid_slot(self):
        """Invalid CC slot raises ValueError."""
        track = MidiPartTrack()

        with pytest.raises(ValueError):
            track.cc_number(0)

        with pytest.raises(ValueError):
            track.cc_number(11)

        with pytest.raises(ValueError):
            track.set_cc_number(0, 64)

    def test_write_returns_correct_size(self):
        """write() returns MIDI_PART_TRACK_SIZE bytes."""
        track = MidiPartTrack()
        data = track.write()

        assert len(data) == MIDI_PART_TRACK_SIZE
        assert isinstance(data, bytes)

    def test_clone(self):
        """clone() creates independent copy."""
        original = MidiPartTrack(
            track_num=1,
            channel=5,
            default_note=60,
        )

        cloned = original.clone()

        # Should have same data
        assert cloned.channel == original.channel
        assert cloned.default_note == original.default_note

        # But be independent
        cloned.channel = 10
        cloned.default_note = 72

        assert original.channel == 5
        assert original.default_note == 60

    def test_equality(self):
        """MidiPartTrack objects with same data are equal."""
        a = MidiPartTrack(track_num=1, channel=5, default_note=60)
        b = MidiPartTrack(track_num=1, channel=5, default_note=60)
        c = MidiPartTrack(track_num=1, channel=5, default_note=72)

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns track properties."""
        track = MidiPartTrack(
            track_num=2,
            channel=5,
            default_note=60,
            default_velocity=80,
        )

        d = track.to_dict()

        assert d["track"] == 2
        assert d["channel"] == 5
        assert d["note"]["default_note"] == 60
        assert d["note"]["default_velocity"] == 80
        assert "cc" in d
        assert "arp" in d

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = MidiPartTrack(
            track_num=3,
            channel=10,
            program=32,
            default_note=48,
        )

        d = original.to_dict()
        restored = MidiPartTrack.from_dict(d)

        assert restored.track_num == original.track_num
        assert restored.channel == original.channel
        assert restored.program == original.program
        assert restored.default_note == original.default_note


class TestMidiPartTrackArp:
    """Tests for MidiPartTrack arpeggiator settings."""

    def test_arp_transpose(self):
        """arp_transpose property works."""
        track = MidiPartTrack()
        track.arp_transpose = 72

        assert track.arp_transpose == 72

    def test_arp_legato(self):
        """arp_legato property works."""
        track = MidiPartTrack()
        track.arp_legato = 64

        assert track.arp_legato == 64

    def test_arp_mode(self):
        """arp_mode property works."""
        track = MidiPartTrack()
        track.arp_mode = 3

        assert track.arp_mode == 3

    def test_arp_speed(self):
        """arp_speed property works."""
        track = MidiPartTrack()
        track.arp_speed = 24

        assert track.arp_speed == 24

    def test_arp_range(self):
        """arp_range property works."""
        track = MidiPartTrack()
        track.arp_range = 2

        assert track.arp_range == 2

    def test_arp_note_length(self):
        """arp_note_length property works."""
        track = MidiPartTrack()
        track.arp_note_length = 12

        assert track.arp_note_length == 12


class TestMidiPartTrackRepr:
    """Tests for MidiPartTrack string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        track = MidiPartTrack(track_num=3, channel=5)

        r = repr(track)
        assert "MidiPartTrack" in r
        assert "track=3" in r
        assert "channel=5" in r


# =============================================================================
# MidiPatternTrack Tests (Phase 2)
# =============================================================================

class TestMidiPatternTrackStandalone:
    """Tests for standalone MidiPatternTrack object."""

    def test_default_construction(self):
        """MidiPatternTrack() creates object with defaults."""
        track = MidiPatternTrack()

        assert track.track_num == 1
        assert track.active_steps == []
        assert track.trigless_steps == []

    def test_constructor_with_active_steps(self):
        """MidiPatternTrack accepts active_steps in constructor."""
        track = MidiPatternTrack(
            track_num=2,
            active_steps=[1, 5, 9, 13],
        )

        assert track.track_num == 2
        assert track.active_steps == [1, 5, 9, 13]

    def test_constructor_with_trigless_steps(self):
        """MidiPatternTrack accepts trigless_steps in constructor."""
        track = MidiPatternTrack(
            track_num=1,
            trigless_steps=[3, 7, 11, 15],
        )

        assert track.trigless_steps == [3, 7, 11, 15]

    def test_step_access(self):
        """step() returns MidiStep for given position."""
        track = MidiPatternTrack()

        step = track.step(5)
        assert isinstance(step, MidiStep)
        assert step.step_num == 5

    def test_step_modification(self):
        """Modifying a step affects the track."""
        track = MidiPatternTrack()

        step = track.step(5)
        step.active = True
        step.note = 60
        step.velocity = 100

        # Step should retain modifications
        assert track.step(5).active == True
        assert track.step(5).note == 60
        assert track.step(5).velocity == 100

    def test_active_steps_setter(self):
        """Setting active_steps updates the track."""
        track = MidiPatternTrack()

        track.active_steps = [1, 2, 3, 4]
        assert track.active_steps == [1, 2, 3, 4]

        # Verify steps are marked active
        assert track.step(1).active == True
        assert track.step(5).active == False

    def test_write_returns_correct_size(self):
        """write() returns MIDI_TRACK_PATTERN_SIZE bytes."""
        track = MidiPatternTrack()
        data = track.write()

        assert len(data) == MIDI_TRACK_PATTERN_SIZE
        assert isinstance(data, bytes)

    def test_read_write_round_trip(self):
        """read(write(x)) preserves data."""
        original = MidiPatternTrack(
            track_num=3,
            active_steps=[1, 5, 9, 13],
            trigless_steps=[2, 6],
        )
        original.step(5).note = 60
        original.step(5).velocity = 100
        original.step(5).condition = TrigCondition.FILL

        data = original.write()
        restored = MidiPatternTrack.read(3, data)

        assert restored.track_num == original.track_num
        assert restored.active_steps == original.active_steps
        assert restored.trigless_steps == original.trigless_steps
        assert restored.step(5).note == 60
        assert restored.step(5).velocity == 100
        assert restored.step(5).condition == TrigCondition.FILL

    def test_clone(self):
        """clone() creates independent copy."""
        original = MidiPatternTrack(
            track_num=1,
            active_steps=[1, 5, 9],
        )

        cloned = original.clone()

        # Should have same data
        assert cloned.active_steps == original.active_steps

        # But be independent
        cloned.active_steps = [2, 6, 10]
        assert original.active_steps == [1, 5, 9]

    def test_equality(self):
        """MidiPatternTrack objects with same data are equal."""
        a = MidiPatternTrack(track_num=1, active_steps=[1, 5, 9])
        b = MidiPatternTrack(track_num=1, active_steps=[1, 5, 9])
        c = MidiPatternTrack(track_num=1, active_steps=[1, 5, 13])

        assert a == b
        assert a != c

    def test_to_dict(self):
        """to_dict() returns track properties."""
        track = MidiPatternTrack(
            track_num=1,
            active_steps=[1, 5, 9, 13],
        )

        d = track.to_dict()

        assert d["track"] == 1
        assert d["active_steps"] == [1, 5, 9, 13]
        assert d["trigless_steps"] == []

    def test_to_dict_with_steps(self):
        """to_dict(include_steps=True) includes step data."""
        track = MidiPatternTrack(active_steps=[1, 5])
        track.step(1).note = 60
        track.step(5).condition = TrigCondition.FILL

        d = track.to_dict(include_steps=True)

        assert "steps" in d
        assert len(d["steps"]) >= 2

    def test_from_dict(self):
        """from_dict() creates equivalent object."""
        original = MidiPatternTrack(
            track_num=2,
            active_steps=[1, 5, 9],
        )

        d = original.to_dict()
        restored = MidiPatternTrack.from_dict(d)

        assert restored.track_num == original.track_num
        assert restored.active_steps == original.active_steps


class TestMidiPatternTrackRepr:
    """Tests for MidiPatternTrack string representation."""

    def test_repr(self):
        """__repr__ shows key properties."""
        track = MidiPatternTrack(track_num=2, active_steps=[1, 5, 9])

        r = repr(track)
        assert "MidiPatternTrack" in r
        assert "track=2" in r
        assert "active_steps=3" in r
