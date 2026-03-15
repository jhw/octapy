# Roadmap

Features not yet supported in octapy's high-level API. Binary offsets may exist in `_io/` but are not exposed or tested. See [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) for reference implementations.

## Machine Types

- **Pickup machines** — Binary offsets defined, SRC param names mapped, but no `configure_pickup()` method, no tests, no demos. Needs: configure method, SRC page validation, test coverage.

## Parameter Pages

- **LFO page (audio tracks)** — Speed/depth offsets exist, but no high-level accessor. LFO setup (parameter targets, waveforms, multipliers, triggers) not mapped at all.
- **LFO page (MIDI tracks)** — Same as audio: offsets exist for speed/depth, setup not mapped.
- **Custom LFO designs** — 16-step custom waveforms per track. Not implemented.

## Patterns

- **MIDI CC p-locks** — CC values can be set at Part level but CC p-locks in patterns are not exposed.
- **Swing trigs** — Offsets exist, no high-level API.
- **Slide trigs** — Offsets exist, no high-level API.
- **Pattern chaining** — Chain behavior not exposed.

## MIDI Tracks

- **Custom arp sequences** — 16-step note sequences per MIDI track. Not implemented.
- **MIDI trig modes** — Per-track trig mode (TRACK vs CHROMATIC). Not exposed.

## Arrangements

The Octatrack's arrangement mode (`arr01.work` - `arr08.work`) is not implemented. This includes:
- Arrangement rows with pattern selection and repeat counts
- Tempo automation per row
- MIDI transpose per row
- Scene/offset automation
- Mute masks
- Loop/Jump/Halt row types

## Project Settings

- **Audio control** — CUE/MAIN mixer, gain, DIR settings
- **Input control** — Gate AB/CD, input delay compensation
- **Sequencer control** — Pattern change chain behavior, auto-silence, LFO auto-trig
- **Memory control** — Recorder memory allocation settings
- **Metronome** — Time signature, preroll, volume, pitch
- **MIDI channels** — Per-track MIDI channel assignments (global config)
- **MIDI control** — CC IN/OUT modes, NOTE IN/OUT modes

## Scenes

- **Crossfader assignments** — Scene XLV assignments not exposed.

## Sample Editor

- **Per-sample settings** (`samples.strd`/`samples.work`) — Trim points, loop points, slice grid, timestretch settings per sample. Partially implemented via markers.
