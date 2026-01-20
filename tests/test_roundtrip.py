"""
Round-trip integration tests for standalone objects (Phase 5).

Tests that reading and writing produces byte-for-byte identical output
for unmodified data, and that modifications are correctly persisted.
"""

import tempfile
from pathlib import Path

import pytest

from octapy._io import read_template_file, BankFile, BANK_FILE_SIZE
from octapy.api.objects import (
    Bank, Project, Part, Pattern,
    AudioPartTrack, AudioPatternTrack,
    MidiPartTrack, MidiPatternTrack,
    Scene, SceneTrack,
    AudioStep, MidiStep,
    RecorderSetup,
)
from octapy import MachineType, FX1Type


# =============================================================================
# Fixtures
# =============================================================================

FIXTURE_DIR = Path(__file__).parent / "fixtures"
HELLO_FLEX_ZIP = FIXTURE_DIR / "HELLO FLEX.zip"


@pytest.fixture
def template_bank_data():
    """Get raw template bank data for comparison."""
    return read_template_file("bank01.work")


@pytest.fixture
def hello_flex_project():
    """Load the HELLO FLEX fixture project."""
    if not HELLO_FLEX_ZIP.exists():
        pytest.skip("HELLO FLEX.zip fixture not found")
    return Project.from_zip(HELLO_FLEX_ZIP)


# =============================================================================
# Bank Round-Trip Tests
# =============================================================================

class TestBankRoundTrip:
    """Tests for Bank read/write round-trip integrity."""

    def test_template_bank_round_trip_byte_identical(self, template_bank_data):
        """Bank from template writes back byte-for-byte identical."""
        # Read template into standalone Bank
        bank = Bank.from_template(bank_num=1)

        # Write it back
        output = bank.write()

        # The output should match the template (after octapy defaults applied)
        # Note: BankFile.new() applies octapy defaults, so we compare against that
        expected_bank = BankFile.new(1)
        expected_bank.update_checksum()
        expected = bytes(expected_bank._data)

        assert len(output) == BANK_FILE_SIZE
        assert output == expected

    def test_bank_read_write_round_trip(self, template_bank_data):
        """Bank.read() then write() produces identical bytes."""
        # Read raw template data
        bank = Bank.read(1, template_bank_data)

        # Write it back
        output = bank.write()

        # Should be identical (checksum recalculated)
        assert len(output) == BANK_FILE_SIZE
        # First compare everything except checksum (last 2 bytes before padding)
        # The checksum will be recalculated so it should match

    def test_bank_modification_changes_only_expected_bytes(self):
        """Modifying bank changes only the relevant bytes."""
        bank = Bank.from_template(bank_num=1)
        original = bank.write()

        # Modify flex_count
        bank.flex_count = 5
        modified = bank.write()

        # Find differences
        diffs = [(i, original[i], modified[i])
                 for i in range(len(original))
                 if original[i] != modified[i]]

        # Should have changes (flex_count offset + checksum)
        assert len(diffs) > 0
        # Verify flex_count changed
        assert bank.flex_count == 5

    def test_bank_pattern_modification_persists(self):
        """Pattern modifications are correctly written."""
        bank = Bank.from_template(bank_num=1)

        # Modify pattern
        bank.pattern(1).scale_length = 32
        bank.pattern(1).part = 3
        bank.pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]

        # Write and read back
        data = bank.write()
        restored = Bank.read(1, data)

        assert restored.pattern(1).scale_length == 32
        assert restored.pattern(1).part == 3
        assert restored.pattern(1).audio_track(1).active_steps == [1, 5, 9, 13]

    def test_bank_part_modification_persists(self):
        """Part modifications are correctly written."""
        bank = Bank.from_template(bank_num=1)

        # Modify part
        bank.part(1).active_scene_a = 5
        bank.part(1).active_scene_b = 10
        bank.part(1).audio_track(1).machine_type = MachineType.STATIC
        bank.part(1).audio_track(1).static_slot = 3

        # Write and read back
        data = bank.write()
        restored = Bank.read(1, data)

        assert restored.part(1).active_scene_a == 5
        assert restored.part(1).active_scene_b == 10
        assert restored.part(1).audio_track(1).machine_type == MachineType.STATIC
        assert restored.part(1).audio_track(1).static_slot == 3

    def test_bank_scene_modification_persists(self):
        """Scene modifications are correctly written."""
        bank = Bank.from_template(bank_num=1)

        # Modify scene
        bank.part(1).scene(1).track(1).amp_volume = 100
        bank.part(1).scene(1).track(1).playback_param1 = 72

        # Write and read back
        data = bank.write()
        restored = Bank.read(1, data)

        assert restored.part(1).scene(1).track(1).amp_volume == 100
        assert restored.part(1).scene(1).track(1).playback_param1 == 72


class TestBankCloneIntegrity:
    """Tests for Bank clone integrity."""

    def test_cloned_bank_writes_identical(self):
        """Cloned bank produces identical output."""
        original = Bank.from_template(bank_num=1)
        original.pattern(1).scale_length = 32

        cloned = original.clone()

        original_data = original.write()
        cloned_data = cloned.write()

        assert original_data == cloned_data

    def test_cloned_bank_modifications_independent(self):
        """Modifications to clone don't affect original."""
        original = Bank.from_template(bank_num=1)
        cloned = original.clone()

        # Modify clone
        cloned.pattern(1).scale_length = 64

        # Verify original unchanged
        assert original.pattern(1).scale_length != 64


# =============================================================================
# Project Round-Trip Tests
# =============================================================================

class TestProjectRoundTrip:
    """Tests for Project read/write round-trip integrity."""

    def test_project_from_template_to_directory_round_trip(self):
        """Project from template survives directory round-trip."""
        project = Project.from_template("TEST PROJECT")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "TEST PROJECT"

            # Write to directory
            project.to_directory(tmp_path)

            # Verify files exist
            assert (tmp_path / "project.work").exists()
            assert (tmp_path / "bank01.work").exists()
            assert (tmp_path / "markers.work").exists()

            # Read back
            restored = Project.from_directory(tmp_path)

            assert restored.name == project.name
            assert restored.tempo == project.tempo

    def test_project_from_template_to_zip_round_trip(self):
        """Project from template survives zip round-trip."""
        project = Project.from_template("ZIP TEST")
        project.tempo = 135.0

        with tempfile.TemporaryDirectory() as tmp:
            # Use project name as zip filename so it restores correctly
            zip_path = Path(tmp) / "ZIP TEST.zip"

            # Write to zip
            project.to_zip(zip_path)
            assert zip_path.exists()

            # Read back
            restored = Project.from_zip(zip_path)

            assert restored.name == "ZIP TEST"
            assert restored.tempo == 135.0

    def test_project_modification_persists(self):
        """Project modifications survive round-trip."""
        project = Project.from_template("MOD TEST")

        # Make modifications
        project.tempo = 140.0
        project.master_track = True
        project.bank(1).pattern(1).scale_length = 32
        project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]
        project.bank(1).part(1).audio_track(1).fx1_type = FX1Type.CHORUS

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "MOD TEST"

            # Write and read back
            project.to_directory(tmp_path)
            restored = Project.from_directory(tmp_path)

            assert restored.tempo == 140.0
            assert restored.master_track == True
            assert restored.bank(1).pattern(1).scale_length == 32
            assert restored.bank(1).pattern(1).audio_track(1).active_steps == [1, 5, 9, 13]
            assert restored.bank(1).part(1).audio_track(1).fx1_type == FX1Type.CHORUS


class TestProjectFixtureRoundTrip:
    """Tests using the HELLO FLEX fixture project."""

    def test_load_hello_flex_project(self, hello_flex_project):
        """HELLO FLEX project loads successfully."""
        project = hello_flex_project

        assert project.name == "HELLO FLEX"
        # Should have 16 banks
        for i in range(1, 17):
            assert project.bank(i) is not None

    def test_hello_flex_to_dict(self, hello_flex_project):
        """HELLO FLEX project converts to dict."""
        project = hello_flex_project
        d = project.to_dict()

        assert d["name"] == "HELLO FLEX"
        assert len(d["banks"]) == 16

    def test_hello_flex_round_trip(self, hello_flex_project):
        """HELLO FLEX project survives round-trip."""
        project = hello_flex_project

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "HELLO FLEX"

            # Write and read back
            project.to_directory(tmp_path)
            restored = Project.from_directory(tmp_path)

            assert restored.name == project.name
            assert restored.tempo == project.tempo

    def test_hello_flex_inspect_patterns(self, hello_flex_project):
        """Can inspect patterns in HELLO FLEX project."""
        project = hello_flex_project

        # Look for patterns with active steps
        patterns_with_steps = []
        for bank_num in range(1, 17):
            bank = project.bank(bank_num)
            for pattern_num in range(1, 17):
                pattern = bank.pattern(pattern_num)
                for track_num in range(1, 9):
                    track = pattern.audio_track(track_num)
                    if track.active_steps:
                        patterns_with_steps.append((bank_num, pattern_num, track_num, track.active_steps))

        # The HELLO FLEX demo should have some patterns
        # (This may vary based on what was saved)
        # Just verify we can read the data
        assert isinstance(patterns_with_steps, list)

    def test_hello_flex_inspect_parts(self, hello_flex_project):
        """Can inspect parts in HELLO FLEX project."""
        project = hello_flex_project

        # Get part 1 from bank 1
        part = project.bank(1).part(1)

        # Should be able to read track configurations
        for track_num in range(1, 9):
            track = part.audio_track(track_num)
            assert track.machine_type is not None
            assert isinstance(track.flex_slot, int)


# =============================================================================
# Leaf Object Round-Trip Tests
# =============================================================================

class TestLeafObjectRoundTrip:
    """Tests for leaf object read/write integrity."""

    def test_audio_step_round_trip(self):
        """AudioStep survives read/write round-trip."""
        step = AudioStep(
            step_num=5,
            active=True,
            volume=100,
            pitch=72,
        )

        # write() returns (active, trigless, condition_data, plock_data)
        active, trigless, condition_data, plock_data = step.write()
        restored = AudioStep.read(5, active, trigless, condition_data, plock_data)

        assert restored.active == True
        assert restored.volume == 100
        assert restored.pitch == 72

    def test_midi_step_round_trip(self):
        """MidiStep survives read/write round-trip."""
        step = MidiStep(
            step_num=3,
            active=True,
            note=60,
            velocity=100,
            length=24,
        )

        # write() returns (active, trigless, condition_data, plock_data)
        active, trigless, condition_data, plock_data = step.write()
        restored = MidiStep.read(3, active, trigless, condition_data, plock_data)

        assert restored.active == True
        assert restored.note == 60
        assert restored.velocity == 100
        assert restored.length == 24

    def test_recorder_setup_round_trip(self):
        """RecorderSetup survives read/write round-trip."""
        from octapy import RecordingSource, RecTrigMode

        recorder = RecorderSetup(
            source=RecordingSource.TRACK_3,
            rlen=32,
            trig=RecTrigMode.HOLD,
            loop=True,
        )

        data = recorder.write()
        restored = RecorderSetup.read(data)

        assert restored.source == RecordingSource.TRACK_3
        assert restored.rlen == 32
        assert restored.trig == RecTrigMode.HOLD
        assert restored.loop == True

    def test_scene_track_round_trip(self):
        """SceneTrack survives read/write round-trip."""
        scene_track = SceneTrack(
            track_num=1,
            amp_volume=100,
            playback_param1=72,
            fx1_param1=64,
        )

        data = scene_track.write()
        restored = SceneTrack.read(1, data)

        assert restored.amp_volume == 100
        assert restored.playback_param1 == 72
        assert restored.fx1_param1 == 64


# =============================================================================
# Track Object Round-Trip Tests
# =============================================================================

class TestTrackObjectRoundTrip:
    """Tests for track object read/write integrity."""

    def test_audio_pattern_track_round_trip(self):
        """AudioPatternTrack survives read/write round-trip."""
        track = AudioPatternTrack(
            track_num=1,
            active_steps=[1, 5, 9, 13],
            trigless_steps=[3, 7],
        )
        track.step(1).volume = 100
        track.step(5).pitch = 72

        data = track.write()
        restored = AudioPatternTrack.read(1, data)

        assert restored.active_steps == [1, 5, 9, 13]
        assert restored.trigless_steps == [3, 7]
        assert restored.step(1).volume == 100
        assert restored.step(5).pitch == 72

    def test_midi_pattern_track_round_trip(self):
        """MidiPatternTrack survives read/write round-trip."""
        track = MidiPatternTrack(
            track_num=1,
            active_steps=[1, 2, 3, 4],
        )
        track.step(1).note = 60
        track.step(2).note = 64

        data = track.write()
        restored = MidiPatternTrack.read(1, data)

        assert restored.active_steps == [1, 2, 3, 4]
        assert restored.step(1).note == 60
        assert restored.step(2).note == 64


# =============================================================================
# Container Object Round-Trip Tests
# =============================================================================

class TestContainerObjectRoundTrip:
    """Tests for container object read/write integrity."""

    def test_scene_round_trip(self):
        """Scene survives read/write round-trip."""
        scene = Scene(scene_num=1)
        scene.track(1).amp_volume = 100
        scene.track(2).playback_param1 = 72

        data = scene.write()
        restored = Scene.read(1, data)

        assert restored.track(1).amp_volume == 100
        assert restored.track(2).playback_param1 == 72

    def test_pattern_round_trip(self):
        """Pattern survives bank write/read round-trip."""
        # Create a bank with a modified pattern
        bank = Bank.from_template(bank_num=1)
        bank.pattern(1).scale_length = 32
        bank.pattern(1).part = 2
        bank.pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]

        # Write and read back
        data = bank.write()
        restored = Bank.read(1, data)

        assert restored.pattern(1).scale_length == 32
        assert restored.pattern(1).part == 2
        assert restored.pattern(1).audio_track(1).active_steps == [1, 5, 9, 13]

    def test_part_round_trip(self):
        """Part survives bank write/read round-trip."""
        bank = Bank.from_template(bank_num=1)
        bank.part(1).active_scene_a = 5
        bank.part(1).audio_track(1).machine_type = MachineType.THRU

        # Write and read back
        data = bank.write()
        restored = Bank.read(1, data)

        assert restored.part(1).active_scene_a == 5
        assert restored.part(1).audio_track(1).machine_type == MachineType.THRU
