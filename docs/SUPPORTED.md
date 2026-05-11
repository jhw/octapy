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
| PICKUP | Yes | `configure_pickup()`, SRC params (pitch/dir/length/gain/op), setup (timestretch) |

### Parameter Pages

| Page | octapy | Notes |
|------|--------|-------|
| SRC (playback) | Yes | pitch, start, length, rate, retrig (1-indexed), retrig_time |
| SRC (setup) | Yes | loop, slice, length_mode, rate_mode, timestretch |
| AMP | Yes | attack, hold, release, volume, balance |
| LFO | Yes | 3 LFOs per track via `track.lfo(n)`: speed, depth, destination, waveform, multiplier, trig_mode |
| FX1 | Yes | All effect types with named params |
| FX2 | Yes | All effect types with named params |

### LFO Details

Each audio and MIDI track has 3 independent LFOs (`track.lfo(1)`, `lfo(2)`, `lfo(3)`).
Each exposes:
- `speed`, `depth` (0-127) — main LFO page values
- `destination` (raw index), `waveform`, `multiplier`, `trig_mode` — LFO setup page
- P-locks: `step.lfo_speed(n)` / `step.lfo_depth(n)` on both audio and MIDI steps
- Scene locks for LFO speed/depth already present via `AudioSceneTrack`

Enums: `LfoWaveform` (TRI, SIN, SQR, SAW, EXP, RMP, RND), `LfoTrigMode` (FREE,
TRIG, HOLD, ONE, HALF).

### Recorder Setup

| Feature | octapy | Notes |
|---------|--------|-------|
| Recording source | Yes | MAIN, CUE, inputs, tracks via `RecordingSource` |
| Recording length | Yes | MAX or step count |
| One-shot mode | Yes | `RecTrigMode.ONE`, `ONE2`, `HOLD` |
| Processing | Yes | fade in/out, gain AB/CD, qrec, qpl |

## MIDI Tracks (Parts)

| Feature | octapy | Notes |
|---------|--------|-------|
| Channel | Yes | 1-16 |
| Default note | Yes | Note assignment |
| Note length | Yes | Quantized values |
| Arpeggiator | Yes | transpose, legato, mode, speed, range, note_length |
| CC1 page | Yes | `cc_value(n)` setup + p-lock via `step.cc(n)` |
| CC2 page | Yes | Same as CC1 (slots 5-10) |
| LFO | Yes | 3 LFOs per MIDI track via `midi_track.lfo(n)`, same shape as audio |

## Patterns

| Feature | octapy | Notes |
|---------|--------|-------|
| Audio triggers | Yes | 64 steps, all trig types |
| MIDI triggers | Yes | 64 steps |
| Trig conditions | Yes | Full enum (FILL, PRE, NEI, probability, loops) |
| P-locks (audio) | Yes | All SRC/AMP/FX params |
| P-locks (MIDI) | Partial | Note/velocity/length/PB/AT in constructor; CC p-locks via `step.cc_value(n)` accessor |
| Per-track length | Yes | length and scale per track |
| Pattern scale | Yes | scale_mode, scale_length, scale_mult |
| Pattern chaining | No | Chain behavior not exposed |
| Swing trigs | Yes | `step.swing`, plus `track.swing_steps = [...]` (audio + MIDI) |
| Slide trigs | Yes | `step.slide`, plus `track.slide_steps = [...]` (audio only) |

## Scenes

| Feature | octapy | Notes |
|---------|--------|-------|
| SRC locks | Yes | All playback params |
| AMP locks | Yes | All amp params |
| LFO locks | Yes | spd1-3, dep1-3 |
| FX1 locks | Yes | All params |
| FX2 locks | Yes | All params |
| Crossfader assign | Yes | `scene.crossfader(track)` / `scene.set_crossfader(track, value)` |

## Project Settings

All fields in project.work are preserved on round-trip. High-level grouped
accessors live under `project.settings`:

| Feature | octapy | Notes |
|---------|--------|-------|
| Tempo | Yes | `settings.tempo` (BPM) |
| Master track | Yes | `settings.master_track` |
| Sample slots | Yes | Flex and Static pools |
| MIDI clock/transport/PC | Yes | `settings.midi_clock_*`, `midi_program_change_*` |
| MIDI per-track channels | Yes | `settings.midi.trig_channels[]`, `set_trig_channel(track, ch)` |
| MIDI routing (CC/note in/out) | Yes | `settings.midi.auto_channel`, `soft_thru`, `audio_trk_cc_in/out` etc. |
| Pattern chain settings | Yes | `settings.pattern_chain.chain_behavior`, `auto_silence_tracks`, `auto_trig_lfos` |
| Audio routing / mixer | Yes | `settings.mixer.main_level`, `cue_level`, `phones_mix`, `gate_ab/cd`, … |
| Metronome | Yes | `settings.metronome.enabled`, `time_signature`, `cue_volume`, … |

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
- Machine types (FLEX, STATIC, THRU, NEIGHBOR)
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
