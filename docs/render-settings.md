# Render Settings

Render settings are octapy-specific transformations applied when saving a project. They are **not saved to Octatrack files** - they control how octapy processes and generates project data at save time.

## Purpose

Render settings eliminate repetitive configuration tasks:

- **Part propagation**: Synchronize machine configs and/or scenes across Parts 1-4 (see [PARTS.md](PARTS.md) for why this matters)
- **Auto-trigs**: Add required trigs for master track and Thru machines
- **Sample normalization**: Normalize sample lengths for rhythmic consistency

## Settings Overview

| Setting | Purpose | Scope |
|---------|---------|-------|
| `propagate_scenes` | Copy scenes Part 1 → Parts 2-4 | Per Bank |
| `propagate_src` | Copy SRC/AMP settings Part 1 → Parts 2-4 | Per Bank |
| `propagate_fx` | Copy FX settings Part 1 → Parts 2-4 | Per Bank |
| `auto_master_trig` | Add T8 trig to active patterns | Per Pattern |
| `auto_thru_trig` | Add trigs to Thru machine tracks | Per Pattern |
| `sample_duration` | Normalize sample lengths to target | Sample processing |

## Usage

```python
project = Project.from_template("MY PROJECT")

# Enable master track (T8 receives sum of T1-7)
project.settings.master_track = True

# Configure render settings
project.render_settings.propagate_scenes = True
project.render_settings.propagate_src = True
project.render_settings.propagate_fx = True
project.render_settings.auto_master_trig = True
project.render_settings.sample_duration = NoteLength.EIGHTH
```

## Part Propagation Settings

These settings synchronize configuration from Part 1 to Parts 2-4. See [PARTS.md](PARTS.md) for detailed use cases and patterns.

| Setting | What it copies |
|---------|----------------|
| `propagate_scenes` | Scene locks (all 16 scenes, all 8 tracks) |
| `propagate_src` | SRC page (pitch, start, length, rate, etc.) + AMP page |
| `propagate_fx` | FX1 and FX2 types and parameters |

All propagation settings:
- Only copy if target Part's settings are at template defaults
- Exclude T8 if `master_track` is enabled
- Are idempotent (safe to run multiple times)

## Auto-Trig Settings

### auto_master_trig

Automatically adds a step 1 trig to track 8 in patterns with audio activity.

The master track (T8) requires a trig to process audio. Without a trig, T8 remains silent even when receiving input from T1-7.

**Behavior**:
- Only applies when `project.settings.master_track = True`
- Only adds trig if pattern has trigs on any of T1-7
- Only adds trig if T8 has no existing trigs

### auto_thru_trig

Automatically adds a step 1 trig to tracks with Thru machines.

Thru machines pass external audio through the Octatrack's effects chain. Like master track, they require a trig to activate.

**Behavior**:
- Scans all tracks in each Part for Thru machine type
- Adds step 1 trig to matching tracks in active patterns
- Only adds trig if track has no existing trigs

### sample_duration

Normalizes sample lengths to a target duration based on project BPM.

This is different from the propagation settings - it processes audio files rather than copying configuration.

**Values**:
- `NoteLength.SIXTEENTH` - 1 step (1/16th note)
- `NoteLength.EIGHTH` - 2 steps (default)
- `NoteLength.QUARTER` - 4 steps (1 beat)
- `NoteLength.HALF` - 8 steps
- `NoteLength.WHOLE` - 16 steps (1 bar)
- `None` - No normalization

See [SAMPLES.md](SAMPLES.md) for details on sample normalization.

## Design Principles

### Non-Overlapping

Each setting has a distinct scope:

- `propagate_scenes`: Scene locks (all 16 scenes, all 8 tracks)
- `propagate_src`: SRC/AMP pages only
- `propagate_fx`: FX pages only
- `auto_master_trig`: T8 pattern trigs only
- `auto_thru_trig`: Thru track pattern trigs only
- `sample_duration`: Audio file processing

### Mutual Consistency

Settings are designed to work together without conflicts:

1. **master_track + propagation**: T8 is automatically excluded from `propagate_src` and `propagate_fx` when `master_track` is enabled.

2. **auto_master_trig + patterns**: Only adds trigs to patterns with existing activity, avoiding trigs in empty patterns.

### Idempotent

Running render settings multiple times produces the same result. Settings check for existing configuration before applying changes.

## Recommended Configuration

```python
project.settings.master_track = True

project.render_settings.propagate_scenes = True
project.render_settings.propagate_src = True
project.render_settings.propagate_fx = True
project.render_settings.auto_master_trig = True
```

For recorder buffer tracks (e.g. the "transition trick"), use `configure_as_recorder()` on individual part tracks. See [RECORDERS.md](RECORDERS.md) for the complete workflow.
