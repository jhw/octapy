# Sample Handling

This document describes how octapy handles samples within the context of a project.

## Overview

Samples in octapy projects are:
1. Bundled within project zip files
2. Normalized to consistent durations based on BPM and note length
3. Copied to project-specific directories on the Octatrack

## Project Structure

When a project is saved as a zip file, it contains:

```
project_name.zip
├── project/           # .work files (OT binary format)
│   ├── project.work
│   ├── markers.work
│   ├── bank01.work
│   ├── ...
│   └── arr08.work
└── samples/           # WAV files (bundled with project)
    ├── kick.wav
    ├── snare.wav
    └── ...
```

## Sample Paths

Octatrack project files reference samples using relative paths. When adding samples via `project.add_sample()`, paths are auto-generated as:

```
../AUDIO/projects/{PROJECT_NAME}/{filename}.wav
```

This path structure assumes the project is at the set root level and samples are in a project-specific subdirectory of the AUDIO pool.

## Deployment to Octatrack

The `tools/copy_project.py` script:

1. Unpacks the project zip file
2. Copies `.work` files to the project directory on the OT
3. Copies samples to `AUDIO/projects/{PROJECT}/` on the OT

```bash
./tools/copy_project.py "MY PROJECT"
```

This ensures the relative paths in project files correctly resolve to the deployed samples.

## Sample Normalization

### Purpose

When using one-shot samples of varying lengths, inconsistent durations can cause rhythmic issues. Sample normalization ensures all samples have a consistent duration based on project tempo.

### Configuration

Set `sample_duration` via render settings:

```python
from octapy import Project, NoteLength

project = Project.from_template("MY PROJECT")
project.tempo = 120.0
project.sample_duration = NoteLength.EIGHTH  # 2 steps = 250ms at 120 BPM
```

### Available Durations

| NoteLength | Steps | Duration at 120 BPM |
|------------|-------|---------------------|
| THIRTY_SECOND | 0.5 | 62ms |
| SIXTEENTH | 1 | 125ms |
| EIGHTH | 2 | 250ms |
| QUARTER | 4 | 500ms |
| HALF | 8 | 1000ms |
| WHOLE | 16 | 2000ms |

Duration formula: `(ticks / 24) * (60 / bpm) * 1000` ms

Where `ticks` is the NoteLength enum value (SIXTEENTH=6, EIGHTH=12, QUARTER=24, etc.)

### Normalization Behavior

When `sample_duration` is set:
- **Long samples**: Trimmed to target duration with 3ms fade-out to avoid clicks
- **Short samples**: Padded with silence to reach target duration
- **Exact length samples**: Copied unchanged

When `sample_duration` is `None`:
- Samples are copied without modification

### Example

```python
# At 124 BPM with SIXTEENTH duration:
# Target = (6/24) * (60/124) * 1000 = 121ms

project = Project.from_template("DRUMS")
project.tempo = 124.0
project.sample_duration = NoteLength.SIXTEENTH

# All samples normalized to ~121ms when saved
project.add_sample("path/to/kick.wav")
project.add_sample("path/to/snare.wav")
project.to_zip("output/DRUMS.zip")
```

## Flex Machine Recommended Defaults

For one-shot sample playback, octapy provides recommended defaults that differ from OT machine defaults.

### What Changes

| Parameter | OT Default | octapy Default | Effect |
|-----------|------------|----------------|--------|
| loop (setup A) | ON (1) | OFF (0) | Sample plays once |
| length_mode (setup C) | OFF (0) | TIME (1) | LEN encoder active |
| length (SRC C) | 0 | 127 | Full sample length |

### Application

These defaults are applied via:

```python
# Factory method
track = AudioPartTrack.flex_with_recommended_defaults(track_num=1, flex_slot=0)

# Or on existing track
track.apply_recommended_flex_defaults()

# Or via configure_as_recorder helper
track.configure_as_recorder(RecordingSource.MAIN)
```

### Why These Defaults?

The OT's default `length_mode=OFF` means the LEN encoder on the SRC page is inactive. With `length_mode=TIME` and `length=127`:

- The LEN encoder controls sample playback length
- Value 127 means "play full sample"
- Combined with normalized samples, each one-shot plays for exactly the intended duration (e.g., 2 steps at EIGHTH)

### Static Machines

These defaults only apply to **Flex machines**. Static machines use the standard OT defaults since they stream from the CF card rather than loading into RAM.

## Sample Reversal

Samples can be played in reverse via the `rate` parameter on the SRC page (encoder D).

### Rate Values

| Value | Effect |
|-------|--------|
| 0 | Full reverse |
| 64 | Stopped |
| 127 | Full speed forward (default) |

### Usage

```python
track = part.flex_track(1)

# Play sample in reverse
track.src.rate = 0

# Normal playback
track.src.rate = 127  # default

# Scene-lock reverse (crossfader morphs between forward and reverse)
scene_a.track(1).rate = 127  # forward
scene_b.track(1).rate = 0    # reverse
```

### Rate Mode Requirement

Reversal only works when `rate_mode` is set to PITCH (the default). If set to TSTR (timestretch), the rate encoder affects timestretch amount instead and cannot reverse.

```python
from octapy import RateMode

# Check/set rate mode (via FUNC+SRC setup page)
track.src_setup.rate_mode = RateMode.PITCH  # allows reverse (default)
track.src_setup.rate_mode = RateMode.TSTR   # timestretch, no reverse
```

## Step Probability

Audio steps support per-step probability via the `TrigCondition` enum. The Octatrack uses fixed probability values (PERCENT_1 through PERCENT_99), not a continuous 0-1 range. See `octapy/api/enums.py` for the full list.

For convenience, octapy provides a `probability` property that accepts floats and quantizes to the nearest valid value:

```python
# Direct enum access
step.condition = TrigCondition.PERCENT_50

# Float-based access (quantizes automatically)
step.probability = 0.5   # Sets PERCENT_50
step.probability = 0.48  # Also sets PERCENT_50 (nearest)

# Clear probability (always trigger)
step.probability = None  # or 1.0
```

The quantization is handled by `probability_to_condition()` in `octapy/api/utils.py`.

## Reference Implementation

octapy's defaults are based on analysis of [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/), an open-source Rust library by Mike Robeson. Template defaults in `octapy/_io/bank.py` document both OT template values and octapy overrides.
