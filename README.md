# octapy

A Python library for reading, writing, and modifying Elektron Octatrack project files.

## Overview

octapy lets you build and edit Octatrack projects (`project.work`, `bank01..16.work`, `markers.work`) programmatically. The Octatrack is a sampler/sequencer/looper by [Elektron](https://www.elektron.se/en/octatrack-mkii-explorer); octapy is a Python port of [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/), an open-source Rust library by [Mike Robeson (dijksterhuis)](https://gitlab.com/dijksterhuis).

What it covers:
- All five audio machine types (Flex, Static, Thru, Neighbor, Pickup)
- Pattern sequencing for 8 audio + 8 MIDI tracks per pattern (16 patterns per bank × 16 banks)
- Parts (4 per bank): machine config, AMP/FX1/FX2 pages, LFOs (3 per track), MIDI channel/note/arp settings
- 16 scenes per part with parameter locks (machine, LFO, AMP, FX1, FX2) and crossfader assignments (XLV)
- Per-step p-locks for audio (volume, pitch, start, length, rate, retrig, retrig_time, sample_lock, slice_index, LFOs) and MIDI (note, velocity, length, pitch_bend, aftertouch, CC1-10, LFOs)
- Trig flags: active, trigless, swing, slide (audio); active, trigless, swing (MIDI)
- Trig conditions: FILL/PRE/NEI/FIRST/probability/pattern-loop (TX_RY)
- Recorder buffer setup (source, rlen, trig mode, qrec, qpl, fades, gains)
- Per-slice markers in `markers.work` (slot 1-128 user samples + 129-136 recorder buffers)
- Every field in `project.work` (mixer, metronome, memory, MIDI ports, pattern chain) preserved on round-trip

What it doesn't cover: arrangements (`arr01..08.work`), custom 16-step LFO designs, custom MIDI arp sequences, per-sample `.ot` setting files. See ot-tools-io for those.

## Install

```bash
pip install -e .
```

Runtime dep: `pydub` (sample-pool handling). Dev deps under the `dev` extra: `pytest`, `pytest-cov`.

## Quick start

```python
from octapy import Project, RecordingSource, FX1Type, FX2Type, TrigCondition

project = Project.from_template("MY-PROJECT")
project.settings.tempo = 124.0
project.settings.master_track = True   # T8 sums T1-7

# Add a sample, configure track 1 as a Flex machine on it
slot = project.add_sample("samples/kick.wav")
project.bank(1).part(1).track(1).configure_flex(slot)

# Sequence — four-on-the-floor on track 1
pattern = project.bank(1).pattern(1)
pattern.audio_track(1).active_steps = [1, 5, 9, 13]

# P-lock a velocity ramp on each kick
for step_num, vol in zip([1, 5, 9, 13], [127, 80, 100, 80]):
    pattern.audio_track(1).step(step_num).volume = vol

# Probabilistic ghost kick on step 11
pattern.audio_track(1).step(11).active = True
pattern.audio_track(1).step(11).probability = 0.5

# Configure track 7 as a transition / resample buffer across the entire
# project (every part of every bank) in one call.
project.configure_recorder_buffer(7, RecordingSource.MAIN)

project.to_zip("tmp/projects/MY-PROJECT.zip")
```

Reading an existing project:

```python
project = Project.from_directory("/Volumes/OCTATRACK/EXISTING")
print(project.name, project.settings.tempo)
for slot in project.sample_pool:
    print(f"  slot {slot.slot_number}: {slot.path}")
```

## API hierarchy

```
Project
├── settings           # Tempo, master_track, plus .mixer / .midi / .metronome / .memory / .pattern_chain groups
├── sample_pool        # Sample slot assignments (Flex + Static)
├── markers            # Slice grids per sample slot
└── Bank (1-16)
    ├── Pattern (1-16)
    │   ├── audio_track(1..8)  # AudioPatternTrack — trigs + per-step p-locks
    │   │   └── step(1..64)    # AudioStep — active, trigless, swing, slide, condition, p-locks
    │   └── midi_track(1..8)   # MidiPatternTrack
    │       └── step(1..64)    # MidiStep — note, velocity, length, CCs
    └── Part (1-4)
        ├── audio_track(1..8)  # AudioPartTrack — machine type, slot, AMP, FX1/2, recorder, lfo(1..3)
        ├── midi_track(1..8)   # MidiPartTrack — channel, default note, arp, lfo(1..3)
        └── scene(1..16)       # Scene — per-track param locks + crossfader (XLV) assignments
```

**Project** is the entry point. Create from template, load from directory or zip.

**Bank** holds 16 patterns + 4 parts. Each pattern references one part for its sound settings.

**Pattern → audio_track/midi_track → step** is the sequencer path. Set `active_steps` to place trigs; mutate individual steps for per-step p-locks and conditions.

**Part → audio_track/midi_track** is the sound design path. Page-style accessors (`track.src`, `track.setup`, `track.amp`, `track.fx1`, `track.fx2`) mirror the device's FUNC+page buttons.

## Machine types

```python
from octapy import MachineType

track = project.bank(1).part(1).track(1)

# Configure helpers handle machine type + sample slot + recommended defaults
track.configure_flex(slot)            # FLEX — RAM-loaded sample playback
track.configure_static(slot)          # STATIC — streaming sample playback
track.configure_thru(in_ab="A_PLUS_B")# THRU — live input routing
track.configure_neighbor()            # NEIGHBOR — extra FX on the previous track
track.configure_pickup()              # PICKUP — live looper

# Page accessors — names are machine-type-aware
track.src.pitch = 64
track.src.length = 100
track.setup.loop = 0          # FLEX/STATIC: loop OFF
track.setup.length_mode = 1   # FLEX/STATIC: TIME
track.amp.attack = 10
track.amp.release = 64
track.fx1.base = 100          # name depends on track.fx1_type
```

## P-locks and conditions

```python
from octapy import TrigCondition

step = pattern.audio_track(1).step(5)
step.volume = 100
step.pitch = 72
step.length = 64
step.condition = TrigCondition.FILL
# Or use the float helper (quantizes to nearest valid percent):
step.probability = 0.5

# Swing and slide trig flags (audio); MIDI has swing only
step.swing = True
step.slide = True

# Sample-lock — change which sample plays on this step
step.sample_lock = other_slot

# MIDI CC p-locks
midi_step = pattern.midi_track(1).step(5)
midi_step.note = 60
midi_step.velocity = 90
midi_step.cc(1).value = 64    # CC1 value lock
midi_step.cc(3).value = 100
```

## LFOs

3 LFOs per audio track and per MIDI track, with speed/depth on the main page and destination/waveform/multiplier/trig_mode on the setup page:

```python
from octapy import LfoWaveform, LfoTrigMode

lfo = project.bank(1).part(1).track(1).lfo(1)
lfo.waveform = LfoWaveform.SIN
lfo.speed = 32
lfo.depth = 100
lfo.destination = 12             # raw OS-dependent index
lfo.multiplier = 7
lfo.trig_mode = LfoTrigMode.TRIG

# Per-step p-locks
pattern.audio_track(1).step(5).lfo(1).speed = 64
pattern.audio_track(1).step(5).lfo(1).depth = 127
```

## Scenes

Each part has 16 scenes (the A/B targets the device's crossfader morphs between). A scene holds parameter locks per track plus per-track crossfader (XLV) assignments:

```python
scene = project.bank(1).part(1).scene(1)

# Parameter locks per track
scene.track(1).amp_volume = 100
scene.track(1).pitch = 72
scene.track(2).fx2_param1 = 64

# Crossfader (XLV) assignments — 0-127 fade amounts per track, or None to clear
scene.set_crossfader(1, 0)       # T1 silent at this scene
scene.set_crossfader(7, 127)     # T7 (e.g. transition track) full
```

## Settings

Project-level settings are organized into groups under `project.settings`:

```python
project.settings.tempo = 124.0
project.settings.master_track = True

# MIDI ports — clock/transport/PC, per-track trig channels, CC routing
project.settings.midi.clock_send = True
project.settings.midi.transport_receive = True
project.settings.midi.set_trig_channel(1, 9)
project.settings.midi.auto_channel = 5

# Mixer — main/cue levels, phones mix, input gates and gains
project.settings.mixer.main_level = 100
project.settings.mixer.cue_level = 110

# Metronome — time sig, volumes, pitch
project.settings.metronome.enabled = True
project.settings.metronome.cue_volume = 64

# Memory — recorder allocation, 24-bit flags
project.settings.memory.record_24bit = True
project.settings.memory.reserved_recorder_count = 4

# Pattern chain — auto-silence, auto-trig LFOs
project.settings.pattern_chain.auto_trig_lfos = True
```

Every field in `project.work` survives a round-trip.

## Recorder buffers — one-line setup

The classic transition-trick / live-resample pattern is one method call:

```python
from octapy import RecordingSource

# Configure track 7 as a recorder buffer in every part of every bank.
# Eager — observable in project state immediately.
project.configure_recorder_buffer(7, RecordingSource.MAIN)

# With a slice grid: divide the buffer into N equal slices, enable slice
# mode, and place N trigs with slice_index p-locks in every pattern that
# already has activity. Call this AFTER setting up your patterns.
project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)
```

When `settings.master_track = True`, two save-time fixups run automatically inside `to_directory()` / `to_zip()`: a step-1 trig is auto-added to track 8 in every pattern with activity, and any recorder source set to `TRACK_8` is rewritten to `MAIN` (the OT can't actually record track-8 output when track 8 is master — this lets you write `TRACK_8` as a logical reference).

## Defaults — octapy baseline vs OT factory

octapy's default values for the SRC and recorder pages differ from the OT's factory values in a small number of places, chosen for programmatic one-shot sample workflows: `length=127`, `length_mode=TIME`, `loop=OFF`, recorder `rlen=16`, `qrec=PLEN`. These are applied consistently whether you construct a track directly, build a project from scratch, or load from template.

If you need byte-for-byte parity with the device's on-device factory state, call `track.reset_to_factory_defaults()` — the escape hatch is symmetric with `apply_recommended_defaults()`.

## Sample slots

```python
from octapy import SamplePool

# Add an individual sample (auto-assigned to next free Flex slot)
slot = project.add_sample("samples/kick.wav")

# Or scan a directory and filter by regex
kicks = SamplePool("samples/drums", r"BD")
kick_slot = project.add_sample(kicks.random())
```

Slots 1-128 are user samples (Flex or Static); slots 129-136 are reserved for the 8 recorder buffers. `configure_recorder_buffer()` and `configure_recorder()` wire the corresponding recorder slot automatically.

## Demos

Runnable scripts under `demos/` produce `.zip` files in `tmp/projects/`:

| Demo | Demonstrates |
|---|---|
| `demos/flex_live.py` | Flex-machine live-transition project: euclidean drum patterns, master_track + auto-master-trig, configure_recorder_buffer for the T7 transition trick |

Run:

```bash
PYTHONPATH=. python demos/flex_live.py
```

## Shipping to the Octatrack

`tools/sync.py` covers the local-to-device loop:

```bash
python tools/sync.py                       # status: local vs remote
python tools/sync.py push project          # copy tmp/projects/*.zip to the OT
python tools/sync.py push project flex     # filter by substring
python tools/sync.py push samples          # copy tmp/samples/*/ to AUDIO/samples/
python tools/sync.py clean local           # remove tmp/projects/*.zip
python tools/sync.py clean remote          # remove projects from the OT (+ AUDIO/projects/<name>)
python tools/sync.py clean samples         # remove sample packs from AUDIO/samples/
```

`-f` skips per-item prompts. Non-interactive stdin auto-confirms. Defaults assume the OT is mounted at `/Volumes/OCTATRACK/Woldo`.

## Project layout

```
octapy/
├── api/
│   ├── enums.py             # MachineType, TrigCondition, NoteLength, MidiNote, FX/Lfo enums, …
│   ├── settings.py          # Settings + grouped sub-objects (mixer/midi/metronome/memory/pattern_chain)
│   ├── sample_pool.py       # SamplePool (directory scan + filter)
│   ├── slot_manager.py      # Sample slot allocation
│   ├── utils.py             # quantize_note_length, probability_to_condition
│   └── core/
│       ├── project.py        # Project — top-level container, configure_recorder_buffer, save pipeline
│       ├── bank.py           # Bank — patterns + parts + flex_count + checksum
│       ├── pattern.py        # Pattern — audio_track / midi_track containers + scale settings
│       ├── part.py           # Part — audio_track / midi_track + scenes
│       ├── scene.py          # Scene — param locks + crossfader (XLV)
│       ├── _page.py          # PageAccessor — named param access shared by SRC/SETUP/AMP/FX
│       ├── _lfo_plock.py     # LfoPlock — step.lfo(n) accessor
│       ├── _trig.py          # 8-byte trig mask <-> step list
│       ├── audio/            # AudioPartTrack, AudioPatternTrack, AudioRecorderSetup,
│       │                     # AudioSceneTrack, AudioStep, AudioLfo
│       └── midi/             # MidiPartTrack, MidiPatternTrack, MidiStep, MidiLfo
├── _io/                     # Low-level binary I/O — BankFile, MarkersFile, ProjectFile (INI)
└── templates/               # Embedded project-template-1.40B.zip (Octatrack factory template)

demos/                       # Runnable scripts
tests/                       # pytest suite
tools/sync.py                # Unified push / clean / status for projects + samples
tools/download_erica_pico_packs.py  # One-off sample-pack downloader
```

## Development

```bash
python -m pytest tests/             # fast suite (~17s)
python -m pytest tests/ --slow      # full suite incl. project save/load roundtrips (~49s)
```

Tests live in `tests/`, organized by area (test_core, test_projects, test_scenes, test_markers, test_banks, test_slots, test_parts, test_templates, test_roundtrip). Slow tests are marked with `@pytest.mark.slow` and skipped by default.

## File format references

- **[ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/)** (Rust) — authoritative spec. Byte offsets, struct layouts, default values, checksum logic. octapy is a port of this.
- **[Elektronauts thread](https://www.elektronauts.com/t/ot-tools-io-open-source-rust-library-for-reading-writing-modifying-octatrack-files/232508)** — community discussion of the Rust library and the binary format.
- **[Rust API docs](https://docs.rs/ot-tools-io/latest/ot_tools_io/index.html)** — reference documentation.
- **[Elektron Octatrack MkII](https://www.elektron.se/en/octatrack-mkii-explorer)** — official hardware.

## License

MIT.

## Credits

Heavily indebted to [Mike Robeson (dijksterhuis)](https://gitlab.com/dijksterhuis) for ot-tools-io — without that Rust reference this Python port would not exist. Thanks also to [Elektron](https://www.elektron.se/) for the Octatrack itself.
