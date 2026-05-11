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

Use the `tools/sync.py` script:

```bash
./tools/sync.py push project "MY PROJECT"
```

This unpacks the zip file, copies the `.work` files to the project directory
on the OT, and copies samples to `AUDIO/projects/{PROJECT}/` on the OT so the
relative paths in the project files resolve correctly.

## Flex Machine Recommended Defaults

For one-shot sample playback, octapy provides recommended defaults that differ from OT machine defaults.

### What Changes

| Parameter | OT Default | octapy Default | Effect |
|-----------|------------|----------------|--------|
| loop (setup A) | ON (1) | OFF (0) | Sample plays once |
| length_mode (setup C) | OFF (0) | TIME (1) | LEN encoder active |
| length (SRC C) | 0 | 127 | Full sample length |

### Application

These defaults are applied automatically by the `configure_*` helpers:

```python
# Configure a flex track with a sample
slot = project.add_sample(kick_sample)
track.configure_flex(slot)

# Configure a recorder track (also uses flex defaults)
track.configure_recorder(RecordingSource.MAIN)
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
track = part.track(1)

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
track.setup.rate_mode = RateMode.PITCH  # allows reverse (default)
track.setup.rate_mode = RateMode.TSTR   # timestretch, no reverse
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
