# octapy — agent guide

Python port of [ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io/) (Rust). Reads, writes, and modifies Elektron Octatrack project files (`project.work`, `bank01..16.work`, `markers.work`).

## Code philosophy

- **No backwards compatibility shims.** When refactoring, delete the old code. No `_old` / `_legacy` suffixes, no `# deprecated` markers, no re-exports of moved modules. The recent history has examples — `RenderSettings`, `TEMPLATE_DEFAULT_*` constants, machine-named `flex_track()` / `static_track()` accessors all got deleted outright rather than aliased.
- **Match the binary spec.** When in doubt about an offset, enum value, default, or struct layout, verify against `/Users/jhw/work/ot-tools-io/ot-tools-io/src/`. That Rust crate is the authoritative reference. The bundled `octapy/templates/project-template-1.40B.zip` is the on-device factory template captured byte-for-byte.
- **Be honest about what each piece is for.** `_io/` is the binary layer, `api/` is the high-level surface. Don't leak `_io` constants into user-facing code unless there's a real reason. Don't add a class when a method on `Project` will do (see `configure_recorder_buffer` — it replaced a god-shaped `RenderSettings` knob).
- **Simple and focused.** Implement what the task needs; don't speculate. Three similar lines beats a premature abstraction.

## Architecture

- **Core library:** `octapy/api/` — `enums.py`, `settings.py`, `sample_pool.py`, `slot_manager.py`, `utils.py`, plus the `core/` subtree (`project.py`, `bank.py`, `pattern.py`, `part.py`, `scene.py`, `_page.py`, `_lfo_plock.py`, `_trig.py`, `audio/`, `midi/`).
- **Low-level binary I/O:** `octapy/_io/` — `BankFile`, `MarkersFile`, `ProjectFile` (text/INI). Each wraps a `bytearray` and exposes typed accessors via offset `IntEnum`s.
- **Tools:** `tools/sync.py` (unified push/clean/status for projects + samples). The one-off Erica Pico downloader lives separately.
- **Templates:** `octapy/templates/project-template-1.40B.zip` — the factory project files bundled into the wheel.

### Hierarchy reflected in the API

```
Project → Bank → Pattern → audio_track/midi_track → step
                ↘ Part → audio_track/midi_track + scene → (track scene locks + XLV)
```

This mirrors the Octatrack's own UI hierarchy. Don't invent intermediate concepts.

### Page accessors (`api/core/_page.py`)

`AudioPartTrack` and `AudioSceneTrack` expose machine-aware page accessors:

```python
track.src.pitch        # FLEX/STATIC: pitch; THRU: in_ab; PICKUP: pitch
track.setup.loop       # FLEX/STATIC: loop mode; PICKUP: timestretch
track.amp.attack       # AMP attack
track.fx1.base         # FX-type-aware (FILTER: base, EQ: freq1, …)
```

The accessor uses the current `machine_type` (or `fx1_type` / `fx2_type`) to look up parameter names from `SRC_PARAM_NAMES` / `SRC_SETUP_PARAM_NAMES` / `FX_PARAM_NAMES`. Adding a new machine or FX type means extending the appropriate dict in `_page.py` and the offset enum in `_io/bank.py`.

### Step accessors

Per-step state lives in three places:

- **Trig flags** — `step.active`, `step.trigless`, `step.swing`, `step.slide` (audio); `swing` only on MIDI. Backed by 8-byte trig masks on the parent track, synced via a callback.
- **Condition** — `step.condition` (TrigCondition enum) or `step.probability` (float, quantizes to nearest valid percent). Stored in a 2-byte condition field per step.
- **P-locks** — 32 bytes per step. `step.volume`, `step.pitch`, `step.start`, etc. on audio; `step.note`, `step.velocity`, `step.cc(n).value`, `step.lfo(n).speed/.depth` on both audio and MIDI. `None` = no lock.

`step.lfo(n)` and `step.cc(n)` return small accessor objects (`LfoPlock`, the CC accessor) for symmetry with `track.lfo(n)` — the shape is uniform across part-tracks and steps.

### Defaults — octapy baseline vs OT factory

Every construction path lands on the **octapy baseline**: `length=127`, `length_mode=TIME`, `loop=OFF` on the SRC page, and the recorder's `rlen=16`, `qrec=PLEN`, sources OFF. These differ from the OT's factory defaults in a small number of fields, chosen for programmatic one-shot sample workflows.

- `_io/bank.py` defines two parallel sets of constants: `OT_FACTORY_*` (the device's factory values, kept as a reference) and `OCTAPY_DEFAULT_*` (what octapy actually writes).
- `BankFile.new()` applies `OCTAPY_DEFAULT_*` across all 64 part-tracks when loading the template.
- `AudioPartTrack._apply_defaults` writes `OCTAPY_DEFAULT_*` for the FLEX machine on standalone construction.
- `AudioRecorderSetup.__init__` writes `OCTAPY_DEFAULT_RECORDER_SETUP`.
- Escape hatch: `track.reset_to_factory_defaults()` flips back to `OT_FACTORY_*` and resets the recorder too. Symmetric with `track.apply_recommended_defaults()`.

If you're tempted to make a path use `OT_FACTORY_*` directly, stop — every construction path should produce identical state. The asymmetry is a load-bearing invariant of the test suite.

### Settings (grouped)

`Settings` exposes grouped accessors that mirror the OT's PROJECT menu:

- Top-level scalars: `tempo`, `master_track`, `write_protected`, `pattern_tempo_enabled`
- `settings.midi` — clock/transport/PC, per-track trig channels, auto channel, CC routing
- `settings.mixer` — main/cue levels, gates, gains, phones mix
- `settings.metronome` — time sig, volumes, pitch
- `settings.memory` — recorder allocation, 24-bit flags
- `settings.pattern_chain` — chain behavior, auto-silence, auto-trig LFOs

Every field in `project.work` round-trips byte-identical with the bundled template (verified by `TestProjectSettingsFullCoverage::test_template_roundtrip_byte_identical`). Adding a new field means: (1) add to `ProjectSettings` dataclass, (2) add to `_SETTINGS_FIELDS` schema, (3) expose on the appropriate group in `api/settings.py`.

### `configure_recorder_buffer` — eager, not lazy

```python
project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)
```

This configures track 7 as a Flex-machine recorder buffer across **all 64 part-tracks** at once, optionally slicing the buffer and placing trigs with slice_index p-locks. Eager — fully applied at call time, observable in project state immediately.

The only thing that runs at save time (`_save_finalize`, triggered by `master_track`) is the auto-master-trig + TRACK_8→MAIN substitution. Those genuinely need late binding (they react to whatever the user did up until save). Nothing else is deferred.

If you find yourself adding a new "render setting" knob: don't. Make it an eager method on `Project`.

## Testing

Tests live in `tests/`, organized by area rather than by class:

- `test_core.py` — most of `api/core/` (AudioStep, MidiStep, AudioPartTrack, MidiPartTrack, pattern tracks, configure_* helpers, LFOs, swing/slide, scene tracks)
- `test_projects.py` — ProjectFile low-level + high-level Settings groups + configure_recorder_buffer
- `test_scenes.py` — Scene + AudioSceneTrack + crossfader (XLV)
- `test_markers.py` — MarkersFile + SlotMarkers + Slice
- `test_banks.py` — BankFile basics + checksums
- `test_slots.py` — SlotManager
- `test_parts.py` — enum quantization helpers
- `test_templates.py` — template file presence + bytes
- `test_roundtrip.py` — full save/load roundtrips (slow)

Use pytest. Slow tests are marked `@pytest.mark.slow` and skipped by default; run with `--slow` for the full pipeline coverage.

```bash
python -m pytest tests/             # fast (~17s)
python -m pytest tests/ --slow      # full (~49s)
python -m pytest tests/ -k Lfo      # filter by name
```

Test density (~1 test per 19 production lines) is appropriate for a binary-format library — there are lots of one-byte-offset bugs to catch. Don't aggressively reduce.

## Binary format notes

- All Octatrack `.work` files are little-endian binary except `project.work` (text/INI, CRLF line endings).
- Bank file: 636113 bytes. 21-byte header + 1-byte version + 16 patterns (36588 bytes each) + 8 parts (6331 bytes each; 4 unsaved + 4 saved) + 4 × 7-byte part names + 2-byte big-endian u16 checksum.
- Per-track in a part: machine type (1B), machine params values (30B = 5 machines × 6B), machine params setup (30B), machine slots (5B), track params values (24B = LFO/AMP/FX1/FX2 × 6B), track params setup (30B = LFO setup 1 + AMP + FX1 + FX2 + LFO setup 2 × 6B), recorder setup (12B).
- Per-track in a pattern: 2338 bytes per audio track, 1196 per MIDI. Trig masks are 8 bytes each (active, trigless, plock, oneshot, swing, slide, recorder). P-locks are 32 bytes × 64 steps = 2048 bytes per audio track.
- Scene XLV (crossfader) assignments are a separate 10-byte block per scene (8 track values + 2 unknown), scattered across the part from the main scene-params block.
- `project.work` round-trips byte-identical with the bundled template. The full schema (40+ fields across SETTINGS, STATES, and SAMPLE sections) lives in `_SETTINGS_FIELDS` / `_STATE_FIELDS` in `_io/project.py`.

When adding a new feature, the workflow is:

1. Find the offset / struct in `/Users/jhw/work/ot-tools-io/ot-tools-io/src/`.
2. Add the offset enum and any constants to the right `_io/` file.
3. Wire scatter/gather in the appropriate `read_from_part` / `write_to_part`.
4. Add a high-level accessor on the right `api/core/` class.
5. Add an enum to `api/enums.py` if the field uses fixed values.
6. Tests: at minimum, a setter→getter round-trip and a binary scatter/gather round-trip through the parent track.
