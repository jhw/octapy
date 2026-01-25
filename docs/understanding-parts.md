# Understanding Parts

Parts are one of the most confusing aspects of the Octatrack. This document explains where Parts fit in the hierarchy, why they create complexity, and how octapy's render settings help manage that complexity.

## Hierarchy

```
Project
└── Bank (16 banks: A-P)
    ├── Pattern (16 patterns per bank)
    │   └── Track (8 audio + 8 MIDI per pattern)
    │       └── Step (64 steps per track)
    │           └── P-locks (per-step parameter overrides)
    │
    └── Part (4 parts per bank)
        ├── Track (8 audio tracks per part)
        │   ├── Machine type (Flex, Static, Thru, Neighbor, Pickup)
        │   ├── Sample slot assignment
        │   ├── SRC page (pitch, start, length, rate, etc.)
        │   ├── AMP page (attack, hold, release, volume, balance)
        │   ├── LFO page (speed, depth, destination, etc.)
        │   ├── FX1 page (type + 6 parameters)
        │   └── FX2 page (type + 6 parameters)
        │
        └── Scene (16 scenes per part)
            └── Track locks (parameter overrides for crossfader)
```

**Key insight**: Parts belong to Banks, not Patterns. A Pattern references a Part (1-4), but the Part's configuration lives at the Bank level.

## The Separation

The Octatrack separates:

- **Pattern data**: Steps, trigs, p-locks (the "what" and "when")
- **Part data**: Machines, sound design, effects, scenes (the "how it sounds")

This separation makes sense conceptually. You can have 16 patterns sharing the same 4 sound configurations (Parts), allowing pattern variations without duplicating machine setup.

## The Problem

Parts contain both **machine configuration** and **scenes**. This means each Bank has:

| Resource | Per Part | Per Bank (4 Parts) |
|----------|----------|-------------------|
| Machine configs | 8 | 32 |
| Scenes | 16 | 64 |

When you switch Parts, **everything changes**:
- All 8 machine types and sample assignments
- All SRC/AMP/LFO settings
- All FX types and parameters
- All 16 scenes and their locks

This creates a maintenance burden. If you want consistent sound design across Parts (the common case), you must manually copy:
- Machine configurations × 8 tracks × 3 target Parts = 24 copies
- Scene locks × 16 scenes × 3 target Parts = 48 copies

Any change to a machine or scene requires updating all 4 Parts to stay consistent.

## When Parts Add Value

Parts become valuable when you intentionally want different configurations:

**Different machines per Part**:
- Part 1: Tracks 1-4 as Flex machines with drum samples
- Part 2: Tracks 1-4 as Thru machines for live input
- Part 3: Tracks 1-4 as Static machines with longer samples
- Part 4: Tracks 1-4 as Neighbor machines for resampling

**Different FX per Part**:
- Part 1: Clean (minimal FX)
- Part 2: Heavy reverb/delay
- Part 3: Distortion and filtering
- Part 4: Experimental (comb filter, lofi)

**Different scenes per Part**:
- Part 1: Subtle volume morphs
- Part 2: Dramatic filter sweeps
- Part 3: Pitch/tempo variations
- Part 4: Breakdown scenes

## The Octapy Solution

Octapy's render settings let you **configure Part 1 once** and **propagate selectively** to Parts 2-4:

```python
# Propagate everything (Parts 2-4 mirror Part 1)
project.render_settings.propagate_src = True
project.render_settings.propagate_fx = True
project.render_settings.propagate_scenes = True
```

This eliminates the copy-paste burden while preserving the ability to use Parts intentionally.

### Selective Propagation

You can enable propagation for some settings but not others:

**Example 1: Same machines, different FX**
```python
project.render_settings.propagate_src = True    # Same sample playback
project.render_settings.propagate_scenes = True # Same scene behavior
# propagate_fx = False (default) - configure FX per Part manually
```

Result: 8 machine configurations, 16 scenes, but 32 unique FX setups (8 × 4 Parts).

**Example 2: Same FX and scenes, different machines**
```python
project.render_settings.propagate_fx = True
project.render_settings.propagate_scenes = True
# propagate_src = False - configure machines per Part manually
```

Result: Different sample assignments per Part, but consistent FX and scene behavior.

**Example 3: Maximum variety**
```python
# All propagation disabled (defaults)
# Configure each Part independently
```

Result: Full access to 32 machine configs, 32 FX setups, 64 scenes per bank.

## Practical Patterns

### Pattern: Consistent Sound Design

Most common use case - you want Parts only for live Part-switching effects (reload, mute state, etc.), not for different sounds.

```python
project.render_settings.propagate_src = True
project.render_settings.propagate_fx = True
project.render_settings.propagate_scenes = True
```

Configure Part 1 completely, Parts 2-4 automatically mirror it.

### Pattern: 32 Flex Machines

Use all 4 Parts to access 32 different samples (8 per Part) while maintaining consistent FX and scenes.

```python
project.render_settings.propagate_fx = True
project.render_settings.propagate_scenes = True

# Part 1: Drums kit A (tracks 1-8)
# Part 2: Drums kit B (tracks 1-8)
# Part 3: Melodic samples (tracks 1-8)
# Part 4: FX/texture samples (tracks 1-8)
```

Switching Parts changes all samples but FX and scenes remain consistent.

### Pattern: FX Variations

Use Parts for dramatic sound changes via different FX, while keeping the same samples.

```python
project.render_settings.propagate_src = True
project.render_settings.propagate_scenes = True

# Part 1: Clean, dry sound
# Part 2: Heavy reverb on all tracks
# Part 3: Distortion and bitcrushing
# Part 4: Filter sweeps and delays
```

### Pattern: Scene Banks

Use Parts to access 64 scenes (16 per Part) for maximum crossfader expression.

```python
project.render_settings.propagate_src = True
project.render_settings.propagate_fx = True

# Part 1: Scenes 1-16 for verse
# Part 2: Scenes 1-16 for chorus
# Part 3: Scenes 1-16 for breakdown
# Part 4: Scenes 1-16 for build/drop
```

## Interaction with Transition Track

When `transition_track` is enabled, T7 is automatically excluded from propagation. This preserves the transition buffer configuration across all Parts, which is critical for seamless live transitions.

```python
project.render_settings.transition_track = True
project.render_settings.propagate_src = True  # Applies to T1-6, T8
project.render_settings.propagate_fx = True   # Applies to T1-6, T8
```

Similarly, T8 is excluded when `master_track` is enabled.

## Summary

| Approach | Machine Configs | FX Configs | Scenes | Use Case |
|----------|-----------------|------------|--------|----------|
| Full propagation | 8 | 8 | 16 | Consistent sound, simple setup |
| Machines only | 32 | 8 | 16 | Multiple sample kits |
| FX only | 8 | 32 | 16 | Sound design variations |
| Scenes only | 8 | 8 | 64 | Maximum crossfader expression |
| No propagation | 32 | 32 | 64 | Full complexity, manual management |

Octapy's render settings let you choose your position on this spectrum, gaining the benefits of Parts without the copy-paste burden.
