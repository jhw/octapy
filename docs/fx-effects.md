# FX (Effects) in Octatrack

This document describes how FX settings are stored in the Octatrack file format.

## Overview

The Octatrack has two effect slots per audio track: **FX1** and **FX2**. Each slot can be assigned an effect type, and each effect has 6 parameters (A-F) whose meaning varies by effect type.

FX1 is limited to non-time-based effects, while FX2 can also use time-based effects (delays and reverbs).

## Storage Locations

FX data is stored in multiple places depending on what aspect is being configured:

| What | Where | Scope |
|------|-------|-------|
| FX Type (FX1/FX2) | Part | Per-track; shared by all patterns using this Part |
| FX Base Parameters | Part (Setup page) | Per-track default values for params A-F |
| Scene FX Parameters | Part (SceneParams) | Per-scene, per-track overrides |
| Active Scenes A/B | Part | Which of 16 scenes is currently active |
| FX P-Locks | Pattern (AudioTrack) | Per-step parameter overrides |

### Hierarchy of Values

When playing back, parameter values are resolved in this order:

```
Step P-Lock > Active Scene Value > Base Part Value
```

## FX Types

### FX1 Types (Non-Time-Based)

| Effect | Value | Notes |
|--------|-------|-------|
| OFF | 0 | No effect |
| FILTER | 4 | Multi-mode filter |
| SPATIALIZER | 5 | Stereo width/panning |
| EQ | 12 | Parametric EQ |
| DJ EQ | 13 | 3-band DJ-style EQ |
| PHASER | 16 | Phase modulation |
| FLANGER | 17 | Flanging effect |
| CHORUS | 18 | Chorus/detune |
| COMB FILTER | 19 | Comb filtering |
| COMPRESSOR | 24 | Dynamics compression |
| LOFI | 25 | Bit reduction/sample rate reduction |

### FX2 Types (All Effects)

FX2 supports all FX1 types plus time-based effects:

| Effect | Value | Notes |
|--------|-------|-------|
| DELAY | 8 | Tempo-synced delay |
| PLATE REVERB | 20 | Plate-style reverb |
| SPRING REVERB | 21 | Spring-style reverb |
| DARK REVERB | 22 | Dark/ambient reverb |

## File Format Details

### Part Block

FX types are stored in the Part block of `bank*.work` files:

- **FX1 types**: 8 bytes at Part offset, one byte per track (tracks 1-8)
- **FX2 types**: 8 bytes at Part offset, one byte per track (tracks 1-8)

Default values: FX1 = 4 (FILTER), FX2 = 8 (DELAY)

### Scene Parameters

Each Part contains 16 scenes. Each scene has `SceneParams` per audio track:

```
SceneParams (per track)
├── machine: 6 params (A-F)
├── lfo: 6 params (A-F)
├── amp: 6 params (A-F)
├── fx1: 6 params (A-F)
├── fx2: 6 params (A-F)
└── unknown fields
```

Value of `255` means "no assignment" (parameter not controlled by scene).

### P-Lock Data (Per Step)

Each step in a pattern has 32 bytes of p-lock data. FX parameters are stored at:

**FX1 Parameters:**
| Parameter | Offset |
|-----------|--------|
| FX1 Param A | 18 |
| FX1 Param B | 19 |
| FX1 Param C | 20 |
| FX1 Param D | 21 |
| FX1 Param E | 22 |
| FX1 Param F | 23 |

**FX2 Parameters:**
| Parameter | Offset |
|-----------|--------|
| FX2 Param A | 24 |
| FX2 Param B | 25 |
| FX2 Param C | 26 |
| FX2 Param D | 27 |
| FX2 Param E | 28 |
| FX2 Param F | 29 |

Value of `255` (PLOCK_DISABLED) means no p-lock is set for that parameter.

## Parameter Names (A-F)

The meaning of parameters A-F varies by effect type. For example:

- **FILTER**: A=Freq, B=Res, C=?, D=?, E=?, F=?
- **DELAY**: A=Time, B=Feedback, C=?, D=?, E=?, F=Mix

**TODO**: Document parameter names for each FX type (requires manual testing or Octatrack manual reference).

## Current octapy Support

| Feature | Status |
|---------|--------|
| FX type read/write | Supported (`PartTrack.fx1_type`, `fx2_type`) |
| FX p-lock offsets | Defined in `PlockOffset` enum |
| Scene FX data | Structure known, API not yet exposed |
| FX Setup page (base params) | Structure known, API not yet exposed |

## References

- Source: [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) `parts.rs` lines 1002-1038
- FX type values from Rust library documentation comments
