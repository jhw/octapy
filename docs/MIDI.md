# MIDI Handling

This document describes how octapy handles MIDI tracks and note parameters.

## Overview

The Octatrack has 8 MIDI tracks (T1-T8 in MIDI mode) that can sequence external gear. Each MIDI track can send notes, CCs, program changes, and arpeggiator patterns.

## Note Length

### NoteLength Enum

MIDI note lengths use the same `NoteLength` enum as sample duration normalization, ensuring consistency across the API.

```python
from octapy import NoteLength

# Set default note length on a MIDI track
midi_track.default_length = NoteLength.EIGHTH  # 2 steps

# Set arpeggiator note length
midi_track.arp_note_length = NoteLength.SIXTEENTH  # 1 step

# P-lock note length on a step
step.length = NoteLength.QUARTER  # 4 steps
```

### Available Values

Values are MIDI ticks at 24 PPQN (Pulses Per Quarter Note). A quarter note = 24 ticks.

| NoteLength | Ticks | Steps | Musical Value |
|------------|-------|-------|---------------|
| THIRTY_SECOND | 3 | 0.5 | 1/32 |
| SIXTEENTH | 6 | 1 | 1/16 |
| EIGHTH | 12 | 2 | 1/8 |
| THREE_SIXTEENTHS | 18 | 3 | 3/16 |
| QUARTER | 24 | 4 | 1/4 |
| FIVE_SIXTEENTHS | 30 | 5 | 5/16 |
| THREE_EIGHTHS | 36 | 6 | 3/8 |
| SEVEN_SIXTEENTHS | 42 | 7 | 7/16 |
| HALF | 48 | 8 | 1/2 |
| NINE_SIXTEENTHS | 54 | 9 | 9/16 |
| FIVE_EIGHTHS | 60 | 10 | 5/8 |
| ELEVEN_SIXTEENTHS | 66 | 11 | 11/16 |
| THREE_QUARTERS | 72 | 12 | 3/4 |
| THIRTEEN_SIXTEENTHS | 78 | 13 | 13/16 |
| SEVEN_EIGHTHS | 84 | 14 | 7/8 |
| FIFTEEN_SIXTEENTHS | 90 | 15 | 15/16 |
| WHOLE | 96 | 16 | 1/1 |
| SEVENTEEN_SIXTEENTHS | 102 | 17 | 17/16 |
| NINE_EIGHTHS | 108 | 18 | 9/8 |
| NINETEEN_SIXTEENTHS | 114 | 19 | 19/16 |
| FIVE_QUARTERS | 120 | 20 | 5/4 |
| TWENTYONE_SIXTEENTHS | 126 | 21 | 21/16 |
| INFINITY | 127 | - | Hold until release |

### Quantization

Raw values are automatically quantized to valid NoteLength values:

```python
# These are equivalent - raw value 10 snaps to EIGHTH (12)
midi_track.default_length = 10
midi_track.default_length = NoteLength.EIGHTH
```

The quantization function in `octapy/api/utils.py` snaps to the nearest valid value from the set: 3, 6, 12, 18, 24, ... 126, 127.

## MIDI Track Parameters

### Note Page (SRC equivalent)

| Encoder | Parameter | Property |
|---------|-----------|----------|
| A | NOTE | `default_note` |
| B | VEL | `default_velocity` |
| C | LEN | `default_length` |
| D | NOT2 | `default_note2` |
| E | NOT3 | `default_note3` |
| F | NOT4 | `default_note4` |

### Arpeggiator

| Parameter | Property |
|-----------|----------|
| Mode | `arp_mode` |
| Speed | `arp_speed` |
| Range | `arp_range` |
| Note Length | `arp_note_length` |

## Unified API Design

The `NoteLength` enum is shared between:

1. **MIDI note lengths** - `default_length`, `arp_note_length`, step p-locks
2. **Sample duration** - `project.sample_duration` for normalization

This unified approach ensures:
- Consistent naming across audio and MIDI domains
- Same musical concepts map to same enum values
- Step-based timing (1/16 = 1 step) works identically everywhere

```python
from octapy import Project, NoteLength

project = Project.from_template("MY PROJECT")

# Sample normalization uses NoteLength
project.sample_duration = NoteLength.EIGHTH  # 2 steps

# MIDI tracks use the same enum
midi_track = project.bank(1).part(1).midi_track(1)
midi_track.default_length = NoteLength.EIGHTH  # 2 steps
```

## Limitations

### No Scene Locks for MIDI CCs

Unlike audio track parameters, MIDI CC values **cannot be locked to scenes**. The Octatrack's crossfader only morphs between scene values for audio track parameters (SRC, AMP, FX1, FX2, LFO).

This means:
- MIDI CC automation requires step p-locks or LFO modulation
- The crossfader has no effect on MIDI CC output
- Scene A/B buttons do not change MIDI CC values

This is a hardware limitation of the Octatrack, not an octapy limitation.
