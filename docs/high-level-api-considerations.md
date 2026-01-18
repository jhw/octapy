# High-Level API Considerations

This document explores potential API enhancements that would wrap Octatrack quirks to provide a saner, more Pythonic interface. The current API faithfully mirrors the OT's UI hierarchy, but both the underlying file format and UI have quirks that could be abstracted away.

## Trade-offs

Each enhancement involves a trade-off:

| Approach | Pros | Cons |
|----------|------|------|
| Mirror OT UI | 1:1 mapping, power-user control | Exposes quirks, steeper learning curve |
| Abstract quirks | Simpler mental model, fewer footguns | Less control, harder to debug on device |

The M8 API (pym8) takes the abstraction approach more aggressively. We could adopt similar patterns selectively.

---

## 1. Scene Horizontal Propagation

### Problem

With 16 scenes per Part × 4 Parts per Bank = 64 scenes per Bank, manually maintaining consistent scenes across Parts becomes tedious.

**Common use case:** You want to switch sounds by switching Parts, but maintain the same scene behavior. Scene 1 should do "filter sweep" regardless of which Part is active.

### Proposed API

```python
bank.propagate_scene(
    source_part=1,
    scene_num=1,
    target_parts=[2, 3, 4],
    mode="strict"  # or "compatible"
)
```

### Propagation Constraints

Scene locks reference encoder destinations. Not all locks can be copied between Parts:

| Param Type | Propagation Safe When |
|------------|----------------------|
| LFO | Always (common to all audio machines) |
| AMP | Always (common to all audio machines) |
| FX1 | Target track has same `fx1_type` |
| FX2 | Target track has same `fx2_type` |
| PLAYBACK | Target track has same `machine_type` |

### Propagation Modes

**Strict mode** (default):
- Validates all 8 tracks have matching machine and FX types
- Raises error if any track configuration differs
- Guarantees complete scene copy

**Compatible mode**:
- Only copies locks that are valid for target configuration
- LFO/AMP always copied
- FX1/FX2 copied only if types match
- PLAYBACK copied only if machine types match
- Silently skips incompatible locks, returns summary

---

## 2. Unified Sample Machine

### Problem

Users must manually choose between Flex and Static machines:

- **Flex**: Loaded into RAM, supports timestretching, limited by RAM (~80MB total)
- **Static**: Streamed from CF card, no timestretching, unlimited size

This distinction is an implementation detail. Users typically just want to "play a sample."

### Proposed API

```python
# Current API (explicit machine choice)
track.machine_type = MachineType.FLEX
track.flex_slot = 1

# Proposed API (auto-selection)
track.sample = "kick.wav"  # API chooses Flex or Static based on file size
```

### Auto-Selection Logic

```python
FLEX_SIZE_THRESHOLD = 8 * 1024 * 1024  # 8MB

def assign_sample(track, sample_path):
    size = sample_path.stat().st_size
    if size <= FLEX_SIZE_THRESHOLD:
        track.machine_type = MachineType.FLEX
        slot = project.add_sample(sample_path, slot_type="FLEX")
        track.flex_slot = slot
    else:
        track.machine_type = MachineType.STATIC
        slot = project.add_sample(sample_path, slot_type="STATIC")
        track.static_slot = slot
```

### Considerations

- User may want to force Static for RAM management even with small files
- User may want Flex for timestretching even with larger files
- Could provide `track.sample = ("kick.wav", "flex")` override syntax

---

## 3. Automatic Neighbor Machine Allocation

### Problem

Each audio track has 2 FX slots (FX1, FX2). To get more FX, users must:

1. Assign a Neighbor machine to an adjacent track
2. Route audio through the neighbor
3. Configure FX on the neighbor track

This is tedious and error-prone.

### Proposed API: 4-Track Grid Mode

```python
# Explicitly configure as 4-track grid
project.configure_grid(mode="4-track")
# Tracks 1-4 are samplers, tracks 5-8 are auto-assigned as their neighbors
```

Result:
- Track 5 = Neighbor of Track 1 (additional FX for Track 1)
- Track 6 = Neighbor of Track 2
- Track 7 = Neighbor of Track 3
- Track 8 = Neighbor of Track 4

### Proposed API: Auto-Neighbor on FX Overflow

```python
# Current API
track1 = part.flex_track(1)
track1.fx1_type = FX1Type.DELAY
track1.fx2_type = FX2Type.REVERB
# Want more FX? Manual neighbor setup required

# Proposed API
track1.add_fx(FX1Type.DELAY)
track1.add_fx(FX2Type.REVERB)
track1.add_fx(FX1Type.CHORUS)  # Auto-allocates neighbor, assigns FX there
```

### Implementation Sketch

```python
def add_fx(self, fx_type):
    if self._fx_count < 2:
        # Assign to this track's FX1 or FX2
        self._assign_local_fx(fx_type)
    else:
        # Find or create neighbor
        neighbor = self._get_or_create_neighbor()
        neighbor._assign_local_fx(fx_type)
```

### Considerations

- Need to track which tracks are "owned" as neighbors
- Neighbor allocation consumes a track slot
- Should warn/error if no tracks available for neighbor
- What happens when removing FX? Auto-deallocate neighbor?

---

## 4. Track-less Incremental API

### Problem

Track indices (1-8) are an implementation detail. Users think in terms of "instruments" or "voices," not track numbers.

Current API:
```python
part.flex_track(1).sample = "kick.wav"
part.flex_track(2).sample = "snare.wav"
part.flex_track(3).sample = "hat.wav"
```

### Proposed API

```python
kick = part.add_sampler("kick.wav")
snare = part.add_sampler("snare.wav")
hat = part.add_sampler("hat.wav")

# Tracks auto-assigned: kick=1, snare=2, hat=3
# References work without knowing indices
kick.volume = 100
```

### Pattern Programming

```python
pattern = bank.pattern(1)

# Current API
pattern.track(1).active_steps = [1, 5, 9, 13]

# Proposed API (using references)
pattern.steps(kick).active = [1, 5, 9, 13]
# Or
kick.sequence(pattern).active_steps = [1, 5, 9, 13]
```

### Considerations

- Significant departure from OT's mental model
- Harder to correlate with device UI during debugging
- M8 API doesn't go this far (still uses track indices)
- Could be opt-in via alternative entry point: `Project.simple()` vs `Project.from_template()`

---

## 5. Other Potential Abstractions

### Part Defaults Propagation

Similar to scene propagation—copy Part track configurations across Parts:

```python
bank.propagate_part_defaults(
    source_part=1,
    target_parts=[2, 3, 4],
    include=["machine_type", "fx1_type", "fx2_type"]  # selective
)
```

### Pattern-Part Binding

Currently patterns reference parts by number. Could make this more explicit:

```python
# Current
pattern.part = 1

# Proposed
pattern.part = part  # Direct reference
# Or
part.add_pattern(pattern)
```

### Sample Slot Abstraction

Already partially implemented via `project.add_sample()`. Could go further:

```python
# Current
slot = project.add_sample("kick.wav", slot_type="FLEX")
track.flex_slot = slot

# Proposed (combined)
track.load_sample("kick.wav")  # Handles slot allocation internally
```

---

## Implementation Priority

Suggested order based on value/complexity ratio:

1. **Scene propagation** — High value, moderate complexity, well-understood
2. **Unified sample machine** — High value, low complexity
3. **Auto-neighbor** — Medium value, moderate complexity
4. **Track-less API** — Uncertain value, high complexity, defer

---

## References

- [pym8](../pym8/) — M8 API for comparison
- [Parts and Scenes discussion](https://www.elektronauts.com/t/parts-and-scenes/154290)
- [Neighbor machine routing](https://www.elektronauts.com/t/neighbor-machine/12345)
