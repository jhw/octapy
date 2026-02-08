# Recorder Buffers

This document describes the Octatrack's recorder buffer system and how octapy handles it.

## Overview

Each of the 8 audio tracks has an associated recorder buffer. Recorder buffers are **global** - they exist at the track level and are not affected by Part-level machine configuration. There are two aspects:

1. **Recording** - capturing audio to the buffer (configured via REC1/REC2 pages)
2. **Playback** - playing the buffer via a Flex machine (configured at Part level)

## Recording Configuration

### REC1 Page (FUNC + REC1)

Hold a track button and press FUNC + REC1 to access recording setup:

| Encoder | Parameter | Description |
|---------|-----------|-------------|
| A | INAB | External input A/B selection |
| B | INCD | External input C/D selection |
| C | RLEN | Recording length in steps (1-63, or 64=MAX) |
| D | TRIG | Recording mode (ONE, ONE2, HOLD) |
| E | SRC3 | Internal source (tracks 1-8 or MAIN) |
| F | LOOP | Loop recording on/off |

**Important**: Only one source (INAB, INCD, or SRC3) should be active at a time.

### REC2 Page (FUNC + REC2)

| Encoder | Parameter | Description |
|---------|-----------|-------------|
| A | FIN | Fade in duration |
| B | FOUT | Fade out duration |
| C | AB | Input gain for A/B |
| D | QREC | Quantize recording start |
| E | QPL | Quantize playback |
| F | CD | Input gain for C/D |

**QREC** (encoder D) is critical - set to **PLEN** for pattern-quantized recording.

### Triggering Recording

- **REC3** triggers recording - hold a track button and press REC3
- Recording is quantized according to QREC setting
- There is a Quick Record global setting that allows REC3 without holding a track button, but this is not yet parameterized in octapy

## Unified Source Property

Since only one recording source should be active at a time, octapy aggregates INAB, INCD, and SRC3 into a single `source` property:

```python
from octapy import RecordingSource

# Set recording source
track.recorder.source = RecordingSource.MAIN        # Record from main output
track.recorder.source = RecordingSource.TRACK_5    # Record from track 5
track.recorder.source = RecordingSource.INPUT_AB   # Record from external A+B

# Available sources
RecordingSource.OFF
RecordingSource.INPUT_AB, INPUT_A, INPUT_B    # External A/B
RecordingSource.INPUT_CD, INPUT_C, INPUT_D    # External C/D
RecordingSource.TRACK_1 through TRACK_8       # Internal tracks
RecordingSource.MAIN                          # Main output
```

Setting the source automatically zeroes the unused source parameters.

## Playback via Flex Machine

Recorder buffers are played back using a Flex machine. The flex slot values 128-135 correspond to recorder buffers 1-8:

```python
# Direct approach
track.machine_type = MachineType.FLEX
track.recorder_slot = 6  # Play recorder buffer 7 (0-indexed)

# Helper method (recommended)
track.configure_as_recorder(RecordingSource.MAIN)
```

The `recorder_slot` and `flex_slot` properties are mutually exclusive - both write to the same underlying byte.

## octapy Defaults

octapy applies recommended defaults that differ from OT template defaults:

| Parameter | OT Default | octapy Default | Reason |
|-----------|------------|----------------|--------|
| INAB | 1 (A+B) | 0 (OFF) | Use unified source property |
| INCD | 1 (C+D) | 0 (OFF) | Use unified source property |
| SRC3 | 9 (MAIN) | 0 (OFF) | Use unified source property |
| RLEN | 64 (MAX) | 15 (displays as 16) | One bar default |
| LOOP | 1 (ON) | 0 (OFF) | One-shot workflow |
| QREC | 255 (OFF) | 0 (PLEN) | Pattern-quantized recording |

These defaults are applied via the recommended defaults system in `octapy/_io/bank.py`.

## Live Resampling Pattern

The most common recorder buffer pattern is live resampling:

1. Configure a Flex track to play its own recorder buffer
2. Set the recorder to record from a different source (e.g., MAIN)
3. Use scenes to crossfade between source tracks and the resample track

```python
# Configure track 7 as a resample track
part.track(7).configure_as_recorder(RecordingSource.MAIN)
```

This method:
- Sets machine type to FLEX
- Points flex slot to this track's recorder buffer (track 7 -> buffer 7)
- Applies recommended flex defaults (length=127, length_mode=TIME, loop=OFF)
- Sets recorder source to the specified target

## Live Transition Setup

A common live performance pattern using recorder buffers for seamless transitions.

### Overview

The "transition trick" (often attributed to Tarekith) allows you to:
1. Capture the current mix to a recorder buffer
2. Crossfade to the captured audio while changing patterns/banks
3. Crossfade back to the new live content

### Track Allocation

| Track | Role | Machine Type |
|-------|------|--------------|
| T1-T6 | Content tracks | Any (Static, Flex, Thru, etc.) |
| T7 | Transition buffer playback | Flex (plays recorder buffer 7) |
| T8 | Master track | Master |

Note: Some performers use T4 instead of T7. Any track works.

### octapy Configuration

```python
project = Project.from_template("MY PROJECT")
project.settings.master_track = True

# Configure T7 as transition buffer across all parts
for bank_num in range(1, 17):
    bank = project.bank(bank_num)
    for part_num in range(1, 5):
        part = bank.part(part_num)
        part.track(7).configure_as_recorder(RecordingSource.MAIN)

        # Scene 1: Normal playback (T1-6 loud, T7 silent)
        scene1 = part.scene(1)
        for tn in range(1, 7):
            scene1.track(tn).amp_volume = 127
        scene1.track(7).amp_volume = 0

        # Scene 2: Transition playback (T1-6 silent, T7 loud)
        scene2 = part.scene(2)
        for tn in range(1, 7):
            scene2.track(tn).amp_volume = 0
        scene2.track(7).amp_volume = 127
```

### Workflow

1. **Capture**: Press REC3 on T7 to record the master output
2. **Engage**: Move crossfader toward Scene 2 - T1-6 fade out, T7 fades in
3. **Change**: While Scene 2 is engaged, change patterns/banks on T1-6
4. **Disengage**: Move crossfader back toward Scene 1 - seamless transition

### Variations

**Recording from specific tracks:**
```python
# Track 3 records from track 2
part.track(3).configure_as_recorder(RecordingSource.TRACK_2)

# Track 6 records from track 5
part.track(6).configure_as_recorder(RecordingSource.TRACK_5)
```

**Multiple transition tracks:**
Dedicate two tracks for overlapping or A/B transitions.

### Performance FX Design

The crossfader morphs all locked parameters simultaneously. Options:

1. **Volume-only scenes** (default) - FX controlled via encoders
2. **FX on T7 in Scene 2** - FX build during transition
3. **Combined** - Both scenes have FX locks

Recommendation: Keep scenes 1-2 as volume-only, optionally add FX to T7 in Scene 2.

### Important Considerations

- Reset T7 effects before transitions (p-lock step 1 to neutral values)
- Keep T7 configuration consistent across all patterns/banks
- Set "Silence tracks" to OFF so loops carry between patterns
- Do not enable "Starts silent" for T7

## References

- [Quick transition trick/live sampling questions](https://www.elektronauts.com/t/quick-transition-trick-live-sampling-questions/56138)
- [Resampling and rearranging the master track](https://www.elektronauts.com/t/resampling-and-rearranging-the-master-track/33802)
- [Recorder buffers for looping and live sampling](https://www.elektronauts.com/t/recorder-buffers-for-looping-and-live-sampling/52853)
