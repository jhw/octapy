# Octapy Issues

Issues discovered during erlbreaks integration that should be fixed in octapy.

## 1. Setting `step.active = True` doesn't work

**Priority:** High

**Status:** FIXED in branch `fix-api-issues`

**Problem:** Setting the `active` property on individual steps didn't immediately update the underlying buffer. The `active_steps` property would not reflect changes until after `write()` was called.

**Previous broken approach:**
```python
step = pattern.track(track_num).step(step_num)
step.active = True
step.volume = 100
# active_steps would not include step_num until write() was called
```

**Fix:** Steps now have a sync callback that immediately updates the track buffer when `active` or `trigless` properties are changed. Both approaches now work identically:

```python
# Approach 1: Set active_steps as list (original working approach)
pattern.track(track_num).active_steps = [1, 5, 9, 13]

# Approach 2: Set individual step.active (now also works)
pattern.track(track_num).step(1).active = True
pattern.track(track_num).step(5).active = True
# active_steps immediately reflects [1, 5]
```

**Files changed:**
- `octapy/api/core/audio/step.py` - Added sync callback mechanism
- `octapy/api/core/audio/pattern_track.py` - Connect sync callback when loading steps
- `octapy/api/core/midi/step.py` - Same fix for MIDI steps
- `octapy/api/core/midi/pattern_track.py` - Same fix for MIDI tracks

---

## 2. Inconsistent slot indexing for `sample_lock`

**Priority:** Medium

**Status:** FIXED in branch `fix-api-issues`

**Problem:** The API had inconsistent indexing conventions for sample slots:

- `project.add_sample()` returns **1-indexed** slots (1-128)
- `track.configure_flex(slot)` expects **1-indexed** (converts internally)
- `step.sample_lock` expected **0-indexed** (client had to convert manually)

**Previous workaround:**
```python
slot = project.add_sample(sample_path)  # Returns 1-indexed (e.g., 1)
track.configure_flex(slot)               # Works - handles conversion
step.sample_lock = slot - 1              # Had to manually convert to 0-indexed
```

**Fix:** `sample_lock` now uses 1-indexed values (1-128) consistent with the rest of the API:

```python
slot = project.add_sample(sample_path)  # Returns 1 (1-indexed)
track.configure_flex(slot)               # Works
step.sample_lock = slot                  # Now works without conversion!
```

**Note:** `sample_lock` now validates input and raises `ValueError` if the value is not in the range 1-128.

**Files changed:**
- `octapy/api/core/audio/step.py` - Updated `sample_lock` property to use 1-indexed values

---

## Testing

New tests added in `tests/test_core.py`:
- `TestAudioStepSampleLock` - 7 tests for sample_lock indexing and validation
- `TestAudioPatternTrackStandalone.test_step_active_immediately_updates_buffer` - Tests immediate buffer sync
- `TestAudioPatternTrackStandalone.test_step_active_with_roundtrip` - Tests write/read roundtrip

All 448 tests pass.
