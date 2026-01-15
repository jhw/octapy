"""
Tests for Part.
"""

import pytest

from octapy import Part, MachineType
from octapy.api.parts import PART_HEADER


class TestPartBasics:
    """Basic Part tests."""

    def test_create_part(self):
        """Test creating a new Part."""
        part = Part(part_id=0)
        assert part is not None

    def test_part_id(self):
        """Test part ID is set correctly."""
        for i in range(4):
            part = Part(part_id=i)
            assert part.part_id == i

    def test_part_header(self):
        """Test part has correct header."""
        part = Part()
        assert part.check_header() is True


class TestPartMachineTypes:
    """Part machine type tests."""

    def test_default_machine_type(self):
        """Test default machine type is STATIC."""
        part = Part()
        for track in range(1, 9):
            assert part.get_machine_type(track) == MachineType.STATIC

    def test_set_machine_type(self):
        """Test setting machine type."""
        part = Part()
        part.set_machine_type(1, MachineType.FLEX)
        assert part.get_machine_type(1) == MachineType.FLEX

    def test_set_all_machine_types(self):
        """Test setting machine types on all tracks."""
        part = Part()
        types = [
            MachineType.FLEX,
            MachineType.STATIC,
            MachineType.THRU,
            MachineType.NEIGHBOR,
            MachineType.PICKUP,
            MachineType.FLEX,
            MachineType.STATIC,
            MachineType.THRU,
        ]

        for track, machine_type in enumerate(types, 1):
            part.set_machine_type(track, machine_type)

        for track, expected in enumerate(types, 1):
            assert part.get_machine_type(track) == expected


class TestPartVolumes:
    """Part volume tests."""

    def test_default_volume(self):
        """Test default volume is 108."""
        part = Part()
        for track in range(1, 9):
            main, cue = part.get_volume(track)
            assert main == 108
            assert cue == 108

    def test_set_volume(self):
        """Test setting volume."""
        part = Part()
        part.set_volume(track=1, main=100, cue=50)

        main, cue = part.get_volume(1)
        assert main == 100
        assert cue == 50

    def test_volume_clamping(self):
        """Test volume values are clamped to 7 bits."""
        part = Part()
        part.set_volume(track=1, main=200, cue=200)  # Over 127

        main, cue = part.get_volume(1)
        assert main <= 127
        assert cue <= 127


class TestPartFX:
    """Part FX tests."""

    def test_default_fx1(self):
        """Test default FX1 is Filter (4)."""
        part = Part()
        for track in range(1, 9):
            assert part.get_fx1_type(track) == 4

    def test_default_fx2(self):
        """Test default FX2 is Delay (8)."""
        part = Part()
        for track in range(1, 9):
            assert part.get_fx2_type(track) == 8

    def test_set_fx_types(self):
        """Test setting FX types."""
        part = Part()
        part.set_fx1_type(track=1, fx_type=12)  # EQ
        part.set_fx2_type(track=1, fx_type=20)  # Plate Reverb

        assert part.get_fx1_type(1) == 12
        assert part.get_fx2_type(1) == 20


class TestPartScenes:
    """Part scene tests."""

    def test_default_scenes(self):
        """Test default active scenes."""
        part = Part()
        assert part.active_scene_a == 0
        assert part.active_scene_b == 8

    def test_set_scenes(self):
        """Test setting active scenes."""
        part = Part()
        part.active_scene_a = 5
        part.active_scene_b = 12

        assert part.active_scene_a == 5
        assert part.active_scene_b == 12

    def test_scene_clamping(self):
        """Test scene values are clamped to 4 bits."""
        part = Part()
        part.active_scene_a = 20  # Over 15
        part.active_scene_b = 20

        assert part.active_scene_a <= 15
        assert part.active_scene_b <= 15


class TestPartSlots:
    """Part slot assignment tests."""

    def test_set_flex_slot(self):
        """Test setting flex slot."""
        part = Part()
        part.set_flex_slot(track=1, slot=5)
        assert part.get_flex_slot(track=1) == 5

    def test_set_static_slot(self):
        """Test setting static slot."""
        part = Part()
        part.set_static_slot(track=1, slot=10)
        assert part.get_static_slot(track=1) == 10

    def test_set_recorder_slot(self):
        """Test setting recorder slot."""
        part = Part()
        part.set_recorder_slot(track=1, slot=129)
        assert part.get_recorder_slot(track=1) == 129

    def test_all_slot_types(self):
        """Test all slot types on one track."""
        part = Part()

        part.set_static_slot(track=1, slot=1)
        part.set_flex_slot(track=1, slot=2)
        part.set_recorder_slot(track=1, slot=129)

        assert part.get_static_slot(track=1) == 1
        assert part.get_flex_slot(track=1) == 2
        assert part.get_recorder_slot(track=1) == 129
