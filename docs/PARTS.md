# Parts

Parts are one of the most confusing aspects of the Octatrack. This document explains where Parts fit in the hierarchy, why they create complexity, and how octapy's render settings help manage that complexity.

## Quick Summary

Parts belong to Banks and sit alongside (but separate from) Patterns. They contain the non-pattern data: machine configurations and scenes. With 4 Parts per Bank, you effectively have 32 machine configs (8 tracks × 4 Parts) and 64 scenes (16 scenes × 4 Parts) per Bank.

Most users stay on Part 1, making it appear you have 8 machines and 16 scenes. Switching Parts to access more requires careful management since both machines AND scenes change simultaneously.

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

## Working with Parts in octapy

Octapy gives you direct access to each Part — there is no
"configure Part 1 and propagate" magic. The Python loop is your
propagation mechanism, and that's enough for most workflows.

### Pattern: Consistent Sound Design

Most common case — you want all 4 Parts to share machines, FX, and
scenes, using Parts only for live Part-switching effects:

```python
for part_num in range(1, 5):
    part = bank.part(part_num)
    for track_num, slot in enumerate(slots, start=1):
        part.track(track_num).configure_flex(slot)
```

### Pattern: 32 Flex Machines

Use all 4 Parts as independent 8-machine banks (32 samples total per
bank, switched live by changing Part):

```python
kits = [drums_a, drums_b, melodic, fx]
for part_num, kit in enumerate(kits, start=1):
    part = bank.part(part_num)
    for track_num, slot in enumerate(kit, start=1):
        part.track(track_num).configure_flex(slot)
```

### Pattern: Same machines, different FX per Part

```python
for part_num in range(1, 5):
    part = bank.part(part_num)
    # Same flex slots in every part
    for t in range(1, 9):
        part.track(t).configure_flex(slots[t - 1])
    # Different FX2 type per part
    part.track(1).fx2_type = (FX2Type.PLATE_REVERB if part_num == 2
                              else FX2Type.OFF)
```

### Pattern: Scene banks

Each Part has its own 16 scenes, so 4 Parts gives you 64 scenes worth
of crossfader expression:

```python
for part_num in range(1, 5):
    part = bank.part(part_num)
    for scene_num in range(1, 17):
        scene = part.scene(scene_num)
        # ... configure scene locks
```

## Interaction with Master Track

When `settings.master_track = True`, track 8 receives the summed output
of tracks 1–7. Octapy handles two save-time side effects:

- A step-1 trig is auto-added to track 8 in every pattern with audio
  activity on tracks 1–7.
- Any recorder source set to `TRACK_8` is rewritten to `MAIN` at save
  time (the OT can't actually record track 8 output when track 8 is
  the master).

You can still configure track 8 like any other track — these fixups
just ensure the master chain actually carries audio. See
[render-settings.md](render-settings.md) for details.
