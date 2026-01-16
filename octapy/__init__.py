"""
octapy - Python library for Elektron Octatrack binary file I/O.

High-level API for creating and manipulating Octatrack projects.

Example:
    from octapy import Project, MachineType, TrigCondition

    # Create a project
    project = Project.from_template("MY PROJECT")

    # Configure a bank
    bank = project.bank(1)

    # Sound configuration via Part -> PartTrack
    part = bank.part(1)
    track = part.track(1)  # Returns PartTrack
    track.machine_type = MachineType.FLEX
    track.flex_slot = 0

    # Sequence programming via Pattern -> PatternTrack -> Step
    pattern = bank.pattern(1)
    pattern.part = 1
    pattern.track(1).active_steps = [1, 5, 9, 13]  # Returns PatternTrack
    pattern.track(1).step(5).condition = TrigCondition.FILL  # Returns Step

    # Add a sample (slot auto-assigned, flex_count auto-updated)
    project.add_sample("../AUDIO/kick.wav")

    # Save
    project.to_zip("output.zip")
"""

# Enums and exceptions
from .api.enums import (
    MachineType,
    FX1Type,
    FX2Type,
    TrigCondition,
    OctapyError,
    SlotLimitExceeded,
    InvalidSlotNumber,
)

# High-level API classes
from .api.project import Project
from .api.bank import Bank
from .api.part import Part, PartTrack
from .api.pattern import Pattern, PatternTrack
from .api.step import Step
from .api.sample_pool import SamplePool

__version__ = "0.1.0"

__all__ = [
    # Core class
    "Project",
    # Wrapper classes
    "Bank",
    "Part",
    "PartTrack",
    "Pattern",
    "PatternTrack",
    "Step",
    # Utilities
    "SamplePool",
    # Enums
    "MachineType",
    "FX1Type",
    "FX2Type",
    "TrigCondition",
    # Exceptions
    "OctapyError",
    "SlotLimitExceeded",
    "InvalidSlotNumber",
]
