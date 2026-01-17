# MIDI Tracks in Octatrack

This document describes how MIDI track data is stored in the Octatrack file format.

## Overview

The Octatrack has 8 MIDI tracks in addition to 8 audio tracks. While the UI presents these as separate "worlds" (press MIDI button to switch), they are stored together in the same file structures.

## Key Insight: MIDI is Not Separate

Despite the UI separation, MIDI and audio data coexist:

- **Same Bank** — `bank*.work` files contain both
- **Same Pattern** — each pattern has 8 audio + 8 MIDI tracks
- **Same Part** — each part configures both audio and MIDI tracks

The MIDI button is purely a UI mode switch, not a data structure boundary.

## File Structure

### Pattern Contains Both Track Types

```
Pattern
├── header: [u8; 8]
├── audio_track_trigs: [AudioTrackTrigs; 8]  ← audio sequencer data
├── midi_track_trigs: [MidiTrackTrigs; 8]    ← MIDI sequencer data
├── scale: PatternScaleSettings
├── chain_behaviour: PatternChainBehavior
├── part_assignment: u8
└── tempo
```

All 16 patterns in a bank follow this structure. There are no "MIDI-only" or "audio-only" patterns.

### Part Contains Both Track Configs

```
Part
├── Audio track configuration
│   ├── audio_track_fx1: [u8; 8]
│   ├── audio_track_fx2: [u8; 8]
│   ├── audio_track_machine_types: [u8; 8]
│   ├── audio_track_params_values: [AudioTrackParamsValues; 8]
│   └── audio_track_params_setup: [AudioTrackParamsSetup; 8]
│
└── MIDI track configuration
    ├── midi_track_params_values: [MidiTrackParamsValues; 8]
    ├── midi_track_params_setup: [MidiTrackParamsSetup; 8]
    ├── midi_tracks_custom_lfos: [CustomLfoDesign; 8]
    └── midi_tracks_arp_seqs: [MidiArpSequence; 8]
```

## MIDI Track Parameters

### Values (Current Parameter State)

Stored in `MidiTrackParamsValues` within the Part:

#### MIDI/Note Page
```
MidiTrackMidiParamsValues
├── note: u8    (default 48 = C3)
├── vel: u8     (default 100)
├── len: u8     (default 6)
├── not2: u8    (default 64 = off)
├── not3: u8    (default 64 = off)
└── not4: u8    (default 64 = off)
```

#### Arp Page
```
MidiTrackArpParamsValues
├── tran: u8    (transpose, default 64 = center)
├── leg: u8     (legato)
├── mode: u8    (arp mode)
├── spd: u8     (speed, default 5)
├── rnge: u8    (range)
└── nlen: u8    (note length, default 6)
```

#### CC1 Page (Pitch Bend, Aftertouch, CC 1-4)
```
MidiTrackCc1ParamsValues
├── pb: u8      (pitch bend, default 64 = center)
├── at: u8      (aftertouch, default 0)
├── cc1: u8     (default 127)
├── cc2: u8     (default 0)
├── cc3: u8     (default 0)
└── cc4: u8     (default 64)
```

#### CC2 Page (CC 5-10)
```
MidiTrackCc2ParamsValues
├── cc5: u8     (default 0)
├── cc6: u8     (default 0)
├── cc7: u8     (default 0)
├── cc8: u8     (default 0)
├── cc9: u8     (default 0)
└── cc10: u8    (default 0)
```

### Setup (Configuration)

Stored in `MidiTrackParamsSetup` within the Part:

#### Note Setup (Channel, Bank, Program)
```
MidiTrackNoteParamsSetup
├── chan: u8    (MIDI channel 0-15, default 0)
├── bank: u8    (bank select, 128 = off)
├── prog: u8    (program change, 128 = off)
└── sbank: u8   (sub-bank, 128 = off)
```

#### Arp Setup
```
MidiTrackArpParamsSetup
├── len: u8     (arp sequence length, default 7)
└── key: u8     (scale key, 0 = off, 1-24 = C through B)
```

#### CC1 Setup (Which CC Numbers)
```
MidiTrackCc1ParamsSetup
├── cc1: u8     (default 7 = Volume)
├── cc2: u8     (default 1 = Mod Wheel)
├── cc3: u8     (default 2 = Breath)
└── cc4: u8     (default 10 = Pan)
```

#### CC2 Setup (Which CC Numbers)
```
MidiTrackCc2ParamsSetup
├── cc5: u8     (default 71)
├── cc6: u8     (default 72)
├── cc7: u8     (default 73)
├── cc8: u8     (default 74)
├── cc9: u8     (default 75)
└── cc10: u8    (default 76)
```

## Setup vs Values

The Octatrack separates configuration from current state:

| Aspect | Setup Page | Values Page |
|--------|------------|-------------|
| **Purpose** | *What* the knobs control | *Current state* of those controls |
| **MIDI Channel** | `chan` in Note Setup | — |
| **CC Assignments** | `cc1`-`cc10` in CC Setup | — |
| **CC Values** | — | `cc1`-`cc10` in CC Values |
| **Stored In** | Part | Part (base) / Pattern (p-locks) |

Example: If CC1 Setup has `cc1 = 74` (filter cutoff), and CC1 Values has `cc1 = 100`, then MIDI CC#74 will be sent with value 100.

## MIDI Track Sequencer Data

Stored in `MidiTrackTrigs` within each Pattern:

```
MidiTrackTrigs
├── header: [u8; 4]           ("MTRA")
├── trig_masks: MidiTrackTrigMasks
├── scale: u8                 (per-track scale in Per Track mode)
├── pattern_settings: PatternTrackSettings
└── plocks: [MidiTrackParameterLocks; 64]
```

### Trig Masks

```
MidiTrackTrigMasks
├── trigs: u64           (which steps have triggers)
├── accent_trigs: u64    (which steps have accent)
├── swing_trigs: u64     (which steps have swing)
├── slide_trigs: u64     (which steps have slide)
└── ... (additional masks)
```

### P-Locks (Per-Step Parameter Locks)

Each step can override MIDI parameters:

```
MidiTrackParameterLocks
├── midi: MidiTrackMidiParamsValues   (note, vel, len, chords)
├── lfo: LfoParamsValues
├── arp: MidiTrackArpParamsValues
├── ctrl1: MidiTrackCc1ParamsValues   (PB, AT, CC1-4)
└── ctrl2: MidiTrackCc2ParamsValues   (CC5-10)
```

Note: The Rust library comments indicate Elektron reused their audio track p-lock structure for MIDI tracks, even though some fields don't apply.

## Custom Arp Sequences

Each MIDI track can have a custom 16-step arp sequence:

```
MidiArpSequence([u8; 16])
```

Stored in `midi_tracks_arp_seqs` array within the Part.

## Hierarchy Summary

```
Project
└── Bank (1-16)
    ├── Pattern (1-16)
    │   ├── AudioTrackTrigs[8]     ← audio sequencer
    │   └── MidiTrackTrigs[8]      ← MIDI sequencer
    │       ├── trig_masks         ← which steps trigger
    │       └── plocks[64]         ← per-step parameter locks
    └── Part (1-4)
        ├── Audio track params     ← machines, FX, samples
        └── MIDI track params      ← channels, notes, CCs, arps
            ├── values[8]          ← current knob positions
            ├── setup[8]           ← channel, CC assignments
            ├── custom_lfos[8]     ← LFO designs
            └── arp_seqs[8]        ← custom arp patterns
```

## Current octapy Support

| Feature | Status |
|---------|--------|
| MIDI track structure | Documented, not yet exposed in API |
| MIDI channel/program | Documented, not yet exposed |
| CC assignments | Documented, not yet exposed |
| MIDI p-locks | Documented, not yet exposed |
| Arp sequences | Documented, not yet exposed |

## References

- Source: [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) `parts.rs` lines 517-735, `patterns.rs` lines 730-940
