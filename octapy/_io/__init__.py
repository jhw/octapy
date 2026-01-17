"""
Low-level file I/O for Octatrack binary formats.

This module provides raw buffer access to Octatrack files.
Use the high-level API in octapy.api.project for user-friendly access.
"""

from .base import (
    OTBlock,
    read_u16_le,
    write_u16_le,
    read_u16_be,
    write_u16_be,
    read_u32_be,
    write_u32_be,
)

from .bank import (
    BankFile,
    BankOffset,
    AudioTrackOffset,
    PatternOffset,
    PartOffset,
    MachineSlotOffset,
    MachineParamsOffset,
    FlexStaticParamsOffset,
    FlexStaticSetupOffset,
    ThruParamsOffset,
    PickupParamsOffset,
    PickupSetupOffset,
    AudioTrackParamsOffset,
    PlockOffset,
    MidiPartOffset,
    MidiTrackValuesOffset,
    MidiTrackSetupOffset,
    MidiTrackTrigsOffset,
    MidiPlockOffset,
    BANK_FILE_SIZE,
    BANK_HEADER,
    BANK_FILE_VERSION,
    PATTERN_SIZE,
    AUDIO_TRACK_SIZE,
    PATTERN_HEADER,
    AUDIO_TRACK_HEADER,
    PART_HEADER,
    PART_BLOCK_SIZE,
    MACHINE_SLOT_SIZE,
    MACHINE_PARAMS_SIZE,
    AUDIO_TRACK_PARAMS_SIZE,
    PLOCK_SIZE,
    NUM_STEPS,
    PLOCK_DISABLED,
    MIDI_TRACK_VALUES_SIZE,
    MIDI_TRACK_SETUP_SIZE,
    MIDI_TRACK_PATTERN_SIZE,
    MIDI_PLOCK_SIZE,
)

from .markers import (
    MarkersFile,
    SlotMarkers,
    MarkersOffset,
    SlotOffset,
    MARKERS_HEADER,
    MARKERS_FILE_VERSION,
    NUM_FLEX_SLOTS,
    NUM_STATIC_SLOTS,
    SLOT_SIZE,
)

from .project import (
    ProjectFile,
    ProjectSettings,
    ProjectState,
    SampleSlot,
    zip_project,
    unzip_project,
    read_template_file,
    extract_template,
)
