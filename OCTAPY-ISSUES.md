# Octapy Issues

Issues discovered during erlbreaks integration that should be fixed in octapy.

## 1. Setting `step.active = True` doesn't work

**Priority:** High

**Problem:** Setting the `active` property on individual steps doesn't correctly write triggers to the binary data. Triggers appear yellow (trigless) or don't play sound.

**Broken approach:**
```python
step = pattern.track(track_num).step(step_num)
step.active = True
step.volume = 100
```

**Working workaround:**
```python
step_nums = [1, 5, 9, 13]  # Collect step numbers first
pattern.track(track_num).active_steps = step_nums  # Set as list

# Then set p-locks
for step_num in step_nums:
    step = pattern.track(track_num).step(step_num)
    step.volume = 100
```

**Expected behavior:** Both approaches should produce identical results. Setting `step.active = True` should update the trig mask in the underlying buffer.

**Likely cause:** The `_sync_step_to_buffer` method is only called during `write()`, but there may be an ordering issue where the step's `active` state isn't being read correctly from the buffer after `active_steps` is set, or the individual property setter isn't triggering a buffer sync.

**Location:** `octapy/api/core/audio/pattern_track.py` and `octapy/api/core/audio/step.py`

---

## 2. Inconsistent slot indexing for `sample_lock`

**Priority:** Medium

**Problem:** The API has inconsistent indexing conventions for sample slots:

- `project.add_sample()` returns **1-indexed** slots (1-128)
- `track.configure_flex(slot)` expects **1-indexed** (converts internally with `slot - 1`)
- `step.sample_lock` expects **0-indexed** (client must convert manually)

**Current workaround:**
```python
slot = project.add_sample(sample_path)  # Returns 1-indexed (e.g., 1)
track.configure_flex(slot)               # Works - handles conversion
step.sample_lock = slot - 1              # Must manually convert to 0-indexed
```

**Expected behavior:** `sample_lock` should accept 1-indexed values like `configure_flex` does, converting internally.

**Location:** `octapy/api/core/audio/step.py` - `sample_lock` setter
