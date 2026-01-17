# Parts and Scenes

This document describes the structure and relationship between Parts and Scenes in the Octatrack, and how they should be modeled in octapy.

## Overview

- **Parts** contain machine configurations, default parameter values, and scenes
- **Scenes** are crossfader destinations that morph parameters from Part defaults
- Scenes belong to Parts, not to Projects or Banks
- Only audio tracks have scenes; MIDI tracks do not

## Hierarchy

```
Project
└── Bank (1-16)
    ├── Pattern (1-16) → references one Part (1-4)
    └── Part (1-4)
        ├── AudioPartTrack (1-8) — machine config, default encoder values
        ├── MidiPartTrack (1-8) — MIDI channel, note, arp settings
        ├── active_scene_a (0-15) — which scene on crossfader left
        ├── active_scene_b (0-15) — which scene on crossfader right
        └── Scene (1-16)
            └── SceneTrack (1-8) — scene parameter locks (audio only)
```

## Scene Count

- **16 scenes per Part**
- 4 Parts per Bank = **64 scenes per Bank**
- 16 Banks per Project = **1024 scenes per Project**

Each Part has its own independent set of 16 scenes. When you switch Parts, you switch to that Part's scene set.

> "As a result of having 4 Parts you can have 64 scenes in a single bank!"
> — [Parts and Scenes - Elektronauts](https://www.elektronauts.com/t/parts-and-scenes/154290)

## No MIDI Scenes

MIDI tracks have Part configuration but **do not have scenes**. The crossfader/scene morphing system only applies to audio tracks.

> "One of the biggest complaints on the MIDI Sequencer side of the device is when using the crossfader to modulate the 8 sample tracks, there is no option for sending corresponding modulations/CC values to MIDI connected devices."
> — [Cross fader scenes and midi cc - Elektronauts](https://www.elektronauts.com/t/cross-fader-scenes-and-midi-cc/4659)

| | Parts | Scenes |
|---|---|---|
| Audio tracks (1-8) | Yes | Yes |
| MIDI tracks (1-8) | Yes | No |

## Scene Structure

A scene is a sparse mapping of `((track, page, encoder), value)` pairs. Each SceneTrack contains:

| Page | Encoders | Common? |
|------|----------|---------|
| PLAYBACK | 6 params | Machine-specific |
| LFO | SPD1, SPD2, SPD3, DEP1, DEP2, DEP3 | Common |
| AMP | ATK, HOLD, REL, VOL, BAL, F | Common |
| FX1 | 6 params | Common |
| FX2 | 6 params | Common |

- **255 = no lock** (use Part default, don't morph this parameter)
- Any other value = scene lock destination

## Machine-Specific Playback Page

The PLAYBACK page encoders differ by machine type:

| Machine | Playback Params |
|---------|-----------------|
| Flex/Static | PTCH, STRT, LEN, RATE, RTRG, RTIM |
| Thru | (input routing params) |
| Neighbor | (neighbor-specific params) |
| Pickup | (pickup-specific params) |

## Proposed API Structure

### Part Hierarchy (existing)

```
part/
├── base.py         # BasePartTrack (ABC)
├── audio.py        # AudioPartTrack (LFO, AMP pages)
├── sampler.py      # SamplerPartTrack (Flex/Static base)
├── flex.py         # FlexPartTrack
├── static.py       # StaticPartTrack
├── thru.py         # ThruPartTrack
├── neighbor.py     # NeighborPartTrack
├── pickup.py       # PickupPartTrack
├── midi.py         # MidiPartTrack
└── part.py         # Part container
```

### Scene Hierarchy (to implement)

```
scene/
├── __init__.py
├── audio.py        # AudioSceneTrack (base - LFO, AMP, FX1, FX2)
├── sampler.py      # SamplerSceneTrack (adds Flex/Static playback)
├── thru.py         # ThruSceneTrack (adds Thru playback)
├── neighbor.py     # NeighborSceneTrack
├── pickup.py       # PickupSceneTrack
└── scene.py        # Scene container
```

### Class Hierarchy

```
AudioSceneTrack (base)
├── LFO page properties (common to all machines)
├── AMP page properties (common)
├── FX1 page properties (common)
├── FX2 page properties (common)
└── Machine-specific subclasses:
    ├── SamplerSceneTrack (playback: pitch, start, len, rate, rtrg, rtim)
    ├── ThruSceneTrack (playback: thru params)
    ├── NeighborSceneTrack (playback: neighbor params)
    └── PickupSceneTrack (playback: pickup params)
```

### Access Pattern

```python
part = bank.part(1)

# Part's active scene assignments
part.active_scene_a  # 0-15
part.active_scene_b  # 0-15

# Access scene
scene = part.scene(5)  # Scene 1-16

# Access scene track (returns machine-specific type based on Part's machine config)
track = scene.track(1)  # Returns SamplerSceneTrack, ThruSceneTrack, etc.

# Scene locks (None = no lock, use Part default)
track.lfo_speed1 = 64      # Common to all machines
track.amp_volume = 100     # Common to all machines
track.pitch = 72           # SamplerSceneTrack only (PLAYBACK page)
```

## Binary Layout

From ot-tools-io `parts.rs`:

```rust
pub struct Part {
    // ... other fields ...
    pub active_scenes: ActiveScenes,           // scene A/B selection
    pub scenes: [SceneParamsArray; 16],        // 16 scenes
    pub scene_xlvs: [SceneXlvAssignments; 16], // per-track volume fades
}

pub struct SceneParamsArray(pub [SceneParams; 8]);  // 8 audio tracks

pub struct SceneParams {
    pub machine: AudioTrackSceneLockPlayback,  // 6 bytes (playback page)
    pub lfo: LfoParamsValues,                   // 6 bytes
    pub amp: AudioTrackAmpParamsValues,         // 6 bytes
    pub fx1: AudioTrackFxParamsValues,          // 6 bytes
    pub fx2: AudioTrackFxParamsValues,          // 6 bytes
    pub unknown_1: u8,
    pub unknown_2: u8,
}
```

## Scene Propagation

### The Problem

With 16 scenes per Part × 4 Parts per Bank = 64 scenes per Bank, manually maintaining consistent scenes across Parts becomes tedious.

**Common use case:** You want to switch sounds by switching Parts, but maintain the same scene behavior. Scene 1 should do "filter sweep" regardless of which Part is active.

### Horizontal Propagation (Bank Level)

Copy a scene from one Part to other Parts within the same Bank:

```python
bank.propagate_scene(
    source_part=1,
    scene_num=1,
    target_parts=[2, 3, 4],
    mode="strict"  # or "compatible"
)
```

### Propagation Constraints

Scene locks reference encoder destinations. Not all locks can be copied to all Parts:

| Param Type | Propagation Safe When |
|------------|----------------------|
| LFO | Always (common to all audio tracks) |
| AMP | Always (common to all audio tracks) |
| FX1 | Target track has same `fx1_type` |
| FX2 | Target track has same `fx2_type` |
| PLAYBACK | Target track has same `machine_type` |

### Propagation Modes

**Strict mode** (default):
- Validates all 8 tracks have matching machine and FX types
- Raises error if any track configuration differs
- Guarantees complete scene copy

```python
bank.propagate_scene(source_part=1, scene_num=1, target_parts=[2, 3, 4], mode="strict")
# Raises ValueError if Part 2 track 1 has different machine type than Part 1 track 1
```

**Compatible mode**:
- Only copies locks that are valid for target configuration
- LFO/AMP always copied
- FX1/FX2 copied only if types match
- PLAYBACK copied only if machine types match
- Silently skips incompatible locks

```python
bank.propagate_scene(source_part=1, scene_num=1, target_parts=[2, 3, 4], mode="compatible")
# Copies what it can, skips incompatible locks
```

### Implementation Notes

The `propagate_scene` method should:

1. For each target Part:
   - For each track (1-8):
     - Check machine type compatibility
     - Check FX1 type compatibility
     - Check FX2 type compatibility
   - Based on mode, either error or filter
2. Copy scene data (raw bytes or property-by-property)
3. Return summary of what was copied/skipped (in compatible mode)

### Future: Vertical Propagation

Copying scenes across Banks (for live sets where banks = songs) is a potential future enhancement but is not in scope for initial implementation. Users can achieve this by:
1. Copying a Bank
2. Using horizontal propagation within each Bank

## References

- [Parts and Scenes - Elektronauts](https://www.elektronauts.com/t/parts-and-scenes/154290)
- [Cross fader scenes and midi cc - Elektronauts](https://www.elektronauts.com/t/cross-fader-scenes-and-midi-cc/4659)
- [Scenes and midi - Elektronauts](https://www.elektronauts.com/t/scenes-and-midi/17779)
- [Banks, Parts And Scenes - Elektron Manual](https://www.manualslib.com/manual/924760/Elektron-Octatrack-Dps-1.html?page=43)
- [ot-tools-io parts.rs](https://gitlab.com/ot-tools/ot-tools-io/) — Rust implementation
