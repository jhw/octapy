# Render Settings

Render settings are octapy-specific transformations applied when saving a project. They are **not saved to Octatrack files** - they control how octapy processes and generates project data at save time.

## Settings Overview

| Setting | Purpose | Scope |
|---------|---------|-------|
| `recorder_track` | Configure a track as recorder buffer | All banks/parts |
| `recorder_slices` | Pre-configure N equal slices on recorder buffer | Per Pattern |
| `sample_duration` | Normalize sample lengths to target | Sample processing |

## Automatic Behavior

### Master Track Trig

When `project.settings.master_track = True`, octapy automatically adds a step 1 trig to track 8 in any pattern with audio activity on tracks 1-7. This ensures the master track processes audio without manual trig management.

No setting is required — enabling the master track is sufficient.

## Usage

```python
project = Project.from_template("MY PROJECT")

# Enable master track (T8 receives sum of T1-7, auto-trig added)
project.settings.master_track = True

# Configure render settings
project.render_settings.sample_duration = NoteLength.EIGHTH
```

### sample_duration

Normalizes sample lengths to a target duration based on project BPM.

**Values**:
- `NoteLength.SIXTEENTH` - 1 step (1/16th note)
- `NoteLength.EIGHTH` - 2 steps (default)
- `NoteLength.QUARTER` - 4 steps (1 beat)
- `NoteLength.HALF` - 8 steps
- `NoteLength.WHOLE` - 16 steps (1 bar)
- `None` - No normalization

See [SAMPLES.md](SAMPLES.md) for details on sample normalization.

### recorder_track

Configure a track as a recorder buffer across all parts/banks.

```python
project.render_settings.recorder_track = (7, RecordingSource.MAIN)
```

### recorder_slices

Pre-configure slices on the recorder buffer with evenly-spaced trigs.

```python
project.render_settings.recorder_slices = 16  # 2, 4, 8, 16, 32, or 64
```

Requires `recorder_track` to be set. See [RECORDERS.md](RECORDERS.md) for the complete workflow.
