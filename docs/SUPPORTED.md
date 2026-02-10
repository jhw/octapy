# Supported Features

This document compares octapy's coverage with the Octatrack's full feature set, using [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) as reference.

## File Types

| File | octapy | Notes |
|------|--------|-------|
| `bank*.work` | Yes | Patterns, parts, scenes |
| `markers.work` | Yes | Sample markers, slices |
| `project.work` | Yes | Settings, sample slots |
| `arr*.work` | No | Arrangements not implemented |

## Audio Tracks (Parts)

### Machine Types

| Machine | octapy | Notes |
|---------|--------|-------|
| FLEX | Yes | Full SRC page support |
| STATIC | Yes | Full SRC page support |
| THRU | Yes | Input routing |
| NEIGHBOR | Yes | Adjacent track routing |
| PICKUP | Yes | Looper (basic) |

### Parameter Pages

| Page | octapy | Notes |
|------|--------|-------|
| SRC (playback) | Yes | pitch, start, length, rate, retrig (1-indexed), retrig_time |
| SRC (setup) | Yes | loop, slice, length_mode, rate_mode, timestretch |
| AMP | Yes | attack, hold, release, volume, balance |
| LFO | Partial | Offsets defined, no high-level API |
| FX1 | Yes | All effect types with named params |
| FX2 | Yes | All effect types with named params |

### LFO Details

LFO offsets exist in `_io/bank.py` but no high-level accessor:
- Speed 1-3 (LFO_SPD1, LFO_SPD2, LFO_SPD3)
- Depth 1-3 (LFO_DEP1, LFO_DEP2, LFO_DEP3)
- LFO setup (destination, waveform, etc.) - not mapped

### Recorder Setup

| Feature | octapy | Notes |
|---------|--------|-------|
| Recording source | Yes | MAIN, CUE, inputs, tracks |
| Recording length | Yes | MAX or step count |
| One-shot mode | No | Not exposed |
| Processing | No | Not exposed |

## MIDI Tracks (Parts)

| Feature | octapy | Notes |
|---------|--------|-------|
| Channel | Yes | 1-16 |
| Default note | Yes | Note assignment |
| Note length | Yes | Quantized values |
| Arpeggiator | Yes | transpose, legato, mode, speed, range, note_length |
| CC1 page | Partial | Offsets defined, no high-level API |
| CC2 page | Partial | Offsets defined, no high-level API |
| LFO | Partial | Offsets defined, no high-level API |

## Patterns

| Feature | octapy | Notes |
|---------|--------|-------|
| Audio triggers | Yes | 64 steps, all trig types |
| MIDI triggers | Yes | 64 steps |
| Trig conditions | Yes | Full enum (FILL, PRE, NEI, probability, loops) |
| P-locks (audio) | Yes | All SRC/AMP/FX params |
| P-locks (MIDI) | Partial | Note, velocity; CC p-locks not exposed |
| Per-track length | Yes | length and scale per track |
| Pattern scale | Yes | scale_mode, scale_length, scale_mult |
| Pattern chaining | No | Chain behavior not exposed |
| Swing trigs | Partial | Offsets exist, no high-level API |
| Slide trigs | Partial | Offsets exist, no high-level API |

## Scenes

| Feature | octapy | Notes |
|---------|--------|-------|
| SRC locks | Yes | All playback params |
| AMP locks | Yes | All amp params |
| LFO locks | Yes | spd1-3, dep1-3 |
| FX1 locks | Yes | All params |
| FX2 locks | Yes | All params |
| Crossfader assign | No | Scene XLV assignments not exposed |

## Project Settings

| Feature | octapy | Notes |
|---------|--------|-------|
| Tempo | Yes | BPM setting |
| Master track | Yes | Enable/disable |
| Sample slots | Yes | Flex and Static pools |
| Audio routing | No | CUE/MAIN settings not exposed |
| MIDI settings | No | Sync, channels, control not exposed |
| Metronome | No | Not exposed |

## Not Implemented

### Arrangements
The Octatrack's arrangement mode (arr01.work - arr08.work) is not implemented. This includes:
- Arrangement rows
- Pattern sequences
- Repeat counts
- Scene/mute automation

### Sample Editor Settings
Per-sample settings (samples.strd/samples.work) are not fully implemented:
- Trim points (partial)
- Loop points
- Slice grid
- Timestretch settings per sample

### Custom LFO Designs
16-step custom LFO waveforms are not exposed.

### MIDI Arp Sequences
Custom 16-step arp sequences are not exposed.

### Project Control Settings
- Audio/Input control pages
- Sequencer control page
- Memory control page
- MIDI control settings

## Quick Reference

### Fully Supported
- Machine types (FLEX, STATIC, THRU, NEIGHBOR, PICKUP)
- SRC/AMP/FX pages with named parameters
- Pattern sequencing (audio and MIDI)
- Trig conditions and probability
- P-locks for audio parameters
- Scenes with parameter locks
- Per-track pattern length
- Sample slot management

### Partially Supported (offsets exist, no high-level API)
- LFO page (audio tracks)
- CC1/CC2 pages (MIDI tracks)
- Swing/slide trigs
- Recorder one-shot/processing

### Not Implemented
- Arrangements
- Pattern chaining
- Crossfader scene assignments
- Project control menus
- Custom LFO designs
- MIDI arp sequences
- Sample editor settings
