# Audio Part Defaults

This document outlines Part-level default parameters for audio tracks, aiming for consistency with MIDI track defaults.

## Machine-Dependent Parameters

**Important:** Audio track parameters vary by machine type. Not all machines expose the same parameters.

| Machine | Has Pitch? | Src Page Purpose |
|---------|------------|------------------|
| **FLEX** | Yes | Sample playback (pitch, tune, start, len) |
| **STATIC** | Yes | Sample streaming (pitch, tune, start, len) |
| **THRU** | No | Input routing (level, balance, input select) |
| **NEIGHBOR** | No | Adjacent track routing |
| **PICKUP** | Partial? | Looper controls (rec level, overdub, etc.) |
| **MASTER** | No | Master output (track 8 only) |

Only FLEX and STATIC machines have traditional pitch/transpose control. THRU passes live audio — you can't transpose an input signal the same way.

## Comparison with MIDI

| Concept | MIDI (MidiAudioPartTrack) | Audio (AudioPartTrack) | Status |
|---------|---------------------|-------------------|--------|
| **Pitch** | `default_note` (0-127) | `pitch` (64 = center) | Missing (FLEX/STATIC only) |
| **Amplitude** | `default_velocity` (0-127) | `volume` (0-127) | Implemented |
| **Duration** | `default_length` (6 = 1/16) | N/A | Not applicable |

Audio samples have inherent duration, so `default_length` has no audio equivalent.

Pitch only applies to sample-based machines (FLEX, STATIC). For THRU/NEIGHBOR, the Src page parameters have different meanings.

## Current Implementation

`AudioPartTrack` currently exposes:

```python
track = part.track(1)
track.volume        # (main, cue) tuple - Part-level default
track.machine_type  # FLEX, STATIC, etc.
track.flex_slot     # Sample slot assignment
track.fx1_type      # Effect type
track.fx2_type      # Effect type
```

## Proposed Addition

### pitch (transpose) — FLEX/STATIC only

Add a `pitch` property to `AudioPartTrack` for the Part-level transpose default.

| Property | Field | Default | Description |
|----------|-------|---------|-------------|
| `pitch` | `src_params.pitch` | 64 | Transpose (64 = center, 0 = -64, 127 = +63) |

This is the Src page, dial A value stored in `AudioTrackParamsValues`.

**Note:** This property only has meaning for FLEX and STATIC machines. For THRU/NEIGHBOR/PICKUP/MASTER, the same byte offset may exist but represents a different parameter (or is unused).

### Design Options

1. **Single property, document limitation**: Expose `pitch` for all tracks, document it only applies to FLEX/STATIC. Simple but potentially confusing.

2. **Validate machine type**: Raise error if accessing `pitch` on non-sample machines. Safer but requires checking machine_type on every access.

3. **Machine-specific subclasses**: Have `FlexAudioPartTrack`, `ThruAudioPartTrack`, etc. with appropriate properties. Most correct but complex.

**Recommendation:** Option 1 for now (document limitation), since the current `volume` property also applies universally without machine validation.

### Implementation

Location: `octapy/api/part.py`

```python
class AudioPartTrack:
    # ... existing properties ...

    @property
    def pitch(self) -> int:
        """
        Get/set the default pitch/transpose (0-127, 64 = center).

        This is the Src page dial A value for FLEX/STATIC machines.
        For other machine types, this byte may have different meaning.
        """
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_PARAMS_VALUES
        track_offset = (self._track_num - 1) * AUDIO_TRACK_PARAMS_SIZE
        return data[offset + track_offset + AudioParamsOffset.PITCH]

    @pitch.setter
    def pitch(self, value: int):
        data = self._part._bank._bank_file._data
        offset = self._part_offset() + PartOffset.AUDIO_TRACK_PARAMS_VALUES
        track_offset = (self._track_num - 1) * AUDIO_TRACK_PARAMS_SIZE
        data[offset + track_offset + AudioParamsOffset.PITCH] = value & 0x7F
```

### Offset Discovery

Need to determine from ot-tools-io or reverse engineering:

- `PartOffset.AUDIO_TRACK_PARAMS_VALUES` — offset to params values array
- `AUDIO_TRACK_PARAMS_SIZE` — size of each track's params block
- `AudioParamsOffset.PITCH` — offset within params block for pitch

Reference: ot-tools-io `parts.rs` AudioTrackParamsValues structure.

### Tests

Location: `tests/test_parts.py`

```python
class TestAudioPartTrackPitch:
    def test_pitch_default_center(self):
        project = Project.from_template("TEST")
        track = project.bank(1).part(1).track(1)
        assert track.pitch == 64  # Center

    def test_pitch_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.bank(1).part(1).track(1).pitch = 76  # +12 semitones
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).part(1).track(1).pitch == 76
```

## API Consistency

After implementation, audio and MIDI Part-level APIs will be consistent:

```python
# Audio track defaults
audio_track = part.track(1)
audio_track.pitch = 76      # Transpose up an octave
audio_track.set_volume(100) # Default volume

# MIDI track defaults
midi_track = part.midi_track(1)
midi_track.default_note = 60      # Middle C
midi_track.default_velocity = 100 # Default velocity
midi_track.default_length = 6     # 1/16 note
```

## Future Considerations

Other Part-level audio defaults that could be exposed (lower priority):

| Page | Property | Description |
|------|----------|-------------|
| Filter | `filter_cutoff` | Default filter cutoff |
| Filter | `filter_resonance` | Default resonance |
| Amp | `amp_attack` | Amplitude envelope attack |
| Amp | `amp_hold` | Amplitude envelope hold |
| Amp | `amp_release` | Amplitude envelope release |
| LFO | `lfo_speed`, `lfo_depth` | LFO defaults |

These are lower priority as they're less commonly set programmatically compared to pitch and volume.

## Files to Modify

| File | Changes |
|------|---------|
| `octapy/_io/bank.py` | Add `AudioParamsOffset` constants |
| `octapy/api/part.py` | Add `pitch` property to `AudioPartTrack` |
| `tests/test_parts.py` | Add pitch roundtrip tests |
