# Render Settings

Render settings are octapy-specific transformations applied when saving a project. They are **not saved to Octatrack files** - they control how octapy processes and generates project data at save time.

## Purpose

The Octatrack stores configuration per-Part (4 Parts per bank, 16 banks = 64 Parts total). Without automation, setting up common patterns requires extensive copy-paste of:

- Scene locks across Parts
- SRC/AMP settings across Parts
- FX configurations across Parts
- Trigs for master/thru tracks across patterns

Render settings eliminate this repetition. Configure Part 1 once, enable propagation, and octapy replicates the configuration to Parts 2-4 automatically.

The exception is `sample_duration`, which serves a different purpose: normalizing sample lengths for rhythmic consistency.

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
project.render_settings.sample_duration = NoteLength.SIXTEENTH
```

## Setting Details

### propagate_scenes

Copies scene locks from Part 1 to Parts 2-4 within each bank.

Scenes define parameter locks for crossfader morphing. Without propagation, switching Parts would lose scene behavior since each Part has independent scene data.

**Behavior**:
- Only copies scenes that have locks defined in Part 1
- Only copies to target Parts where the scene is blank
- Preserves any manually-configured scenes in Parts 2-4

### propagate_src

Copies SRC (playback) and AMP (envelope) page settings from Part 1 to Parts 2-4.

**SRC page parameters**:
- pitch, start, length, rate, retrig, retrig_time
- loop_mode, slice_mode, length_mode, rate_mode
- timestretch_mode, timestretch_sensitivity

**AMP page parameters**:
- attack, hold, release, volume, balance

**Behavior**:
- Only copies if target Part's settings are at template defaults
- Excludes T8 if `master_track` is enabled

### propagate_fx

Copies FX1 and FX2 settings from Part 1 to Parts 2-4.

**Parameters copied**:
- FX type (filter, delay, reverb, etc.)
- All 6 FX parameters per slot

**Behavior**:
- Only copies if target Part's FX types match template defaults (FX1=FILTER, FX2=DELAY)
- Excludes T8 if `master_track` is enabled

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
- `NoteLength.EIGHTH` - 2 steps
- `NoteLength.QUARTER` - 4 steps (1 beat)
- `NoteLength.HALF` - 8 steps
- `NoteLength.WHOLE` - 16 steps (1 bar)
- `None` - No normalization (default)

**Use case**: When loading one-shot samples of varying lengths, normalizing to a consistent duration (e.g., 1/16th) ensures predictable rhythmic behavior.

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

For recorder buffer tracks (e.g. the "transition trick"), use `configure_as_recorder()` on individual part tracks. See `docs/live-transition-setup.md` for the complete workflow.
