# FX Implementation

This document describes the architecture for implementing FX1/FX2 pages using a container pattern that provides type-safe access to effect-specific parameters.

## The Problem

FX1 and FX2 pages have many different effect types, each with different parameter meanings for the same 6 encoders:

| FX Type | Param 1 | Param 2 | Param 3 | Param 4 | Param 5 | Param 6 |
|---------|---------|---------|---------|---------|---------|---------|
| Filter | Cutoff | Resonance | ... | ... | ... | ... |
| Delay | Time | Feedback | ... | ... | ... | ... |
| Reverb | Decay | Damp | ... | ... | ... | ... |
| Compressor | Threshold | Ratio | ... | ... | ... | ... |

Adding all variants to the base Part class would create massive bloat. We need a pattern that:
1. Provides type-specific property names (not generic `fx1_param1`)
2. Only exposes properties valid for the current FX type
3. Cascades type safety to Scenes automatically
4. Keeps FX code testable in isolation

## Available FX Types

From `enums.py`:

```python
class FX1Type(IntEnum):
    OFF = 0
    FILTER = 4
    SPATIALIZER = 5
    EQ = 12
    DJ_EQ = 13
    PHASER = 16
    FLANGER = 17
    CHORUS = 18
    COMB_FILTER = 19
    COMPRESSOR = 24
    LOFI = 25

class FX2Type(IntEnum):
    # Same as FX1, plus:
    DELAY = 8
    PLATE_REVERB = 20
    SPRING_REVERB = 21
    DARK_REVERB = 22
```

## Solution: FX Container Pattern

Instead of embedding all FX properties in Part classes, use a container pattern where `track.fx1` returns an FX-type-specific object.

### Part Access

```python
track = part.track(1)

# FX type is set on the track
track.fx1_type = FX1Type.FILTER

# Accessing fx1 returns type-specific container
fx = track.fx1          # Returns FilterFX instance
fx.cutoff = 64          # ✓ Valid - Filter has cutoff
fx.resonance = 80       # ✓ Valid - Filter has resonance
fx.delay_time = 50      # ✗ AttributeError - Filter doesn't have delay_time
```

### Scene Access

Scenes automatically inherit the Part's FX type configuration:

```python
scene = part.scene(5)
scene_track = scene.track(1)

# Scene checks Part's FX1 type for this track
scene_fx = scene_track.fx1    # Returns FilterSceneFX (matching Part's FX type)
scene_fx.cutoff = 100         # ✓ Valid scene lock
scene_fx.delay_time = 50      # ✗ AttributeError - impossible to set invalid lock
```

This ensures Part and Scene stay in sync by design.

## Proposed File Structure

```
octapy/api/
├── fx/
│   ├── __init__.py       # Re-exports, factory functions
│   ├── base.py           # BaseFX, BaseSceneFX (ABC)
│   ├── filter.py         # FilterFX, FilterSceneFX
│   ├── delay.py          # DelayFX, DelaySceneFX
│   ├── reverb.py         # PlateReverbFX, SpringReverbFX, DarkReverbFX + Scene variants
│   ├── compressor.py     # CompressorFX, CompressorSceneFX
│   ├── eq.py             # EqFX, DjEqFX + Scene variants
│   ├── modulation.py     # PhaserFX, FlangerFX, ChorusFX, CombFilterFX + Scene variants
│   ├── spatial.py        # SpatializerFX, SpatializerSceneFX
│   └── lofi.py           # LofiFX, LofiFSceneFX
```

## Class Hierarchy

### Part FX Classes

```
BaseFX (ABC)
├── _part_track reference
├── _slot (1 or 2 for FX1/FX2)
├── _get_param(offset) → int
├── _set_param(offset, value)
│
├── FilterFX
│   ├── cutoff
│   ├── resonance
│   └── ...
├── DelayFX
│   ├── delay_time
│   ├── feedback
│   └── ...
├── PlateReverbFX / SpringReverbFX / DarkReverbFX
│   ├── decay
│   ├── damp
│   └── ...
└── ... (other FX types)
```

### Scene FX Classes

```
BaseSceneFX (ABC)
├── _scene_track reference
├── _slot (1 or 2)
├── _get_lock(offset) → Optional[int]  # None = no lock (255)
├── _set_lock(offset, value: Optional[int])
│
├── FilterSceneFX
│   ├── cutoff → Optional[int]
│   └── ...
├── DelaySceneFX
│   ├── delay_time → Optional[int]
│   └── ...
└── ... (matching Part FX types)
```

## Factory Pattern

The Part and Scene track classes use factories to return the correct FX type:

### In AudioPartTrack (or BasePartTrack)

```python
@property
def fx1(self) -> BaseFX:
    """Return FX1 container based on current FX1 type."""
    fx_type = self.fx1_type
    return _create_fx(self, slot=1, fx_type=fx_type)

@property
def fx2(self) -> BaseFX:
    """Return FX2 container based on current FX2 type."""
    fx_type = self.fx2_type
    return _create_fx(self, slot=2, fx_type=fx_type)
```

### In AudioSceneTrack (or BaseSceneTrack)

```python
@property
def fx1(self) -> BaseSceneFX:
    """Return FX1 scene container based on Part's FX1 type."""
    # Get the Part's FX1 type for this track
    part = self._scene._part
    part_track = part.track(self._track_num)
    fx_type = part_track.fx1_type
    return _create_scene_fx(self, slot=1, fx_type=fx_type)
```

### Factory Function

```python
# In fx/__init__.py

_FX_CLASS_MAP = {
    FX1Type.FILTER: FilterFX,
    FX1Type.DELAY: DelayFX,
    FX1Type.PLATE_REVERB: PlateReverbFX,
    # ... etc
}

_SCENE_FX_CLASS_MAP = {
    FX1Type.FILTER: FilterSceneFX,
    FX1Type.DELAY: DelaySceneFX,
    # ... etc
}

def _create_fx(part_track, slot: int, fx_type: int) -> BaseFX:
    cls = _FX_CLASS_MAP.get(fx_type, OffFX)
    return cls(part_track, slot)

def _create_scene_fx(scene_track, slot: int, fx_type: int) -> BaseSceneFX:
    cls = _SCENE_FX_CLASS_MAP.get(fx_type, OffSceneFX)
    return cls(scene_track, slot)
```

## Binary Layout

FX parameters are stored in the Part's track data. From `_io/bank.py`:

```python
class AudioTrackParamsOffset(IntEnum):
    # Within each track's 24-byte params block:
    LFO_SPD1 = 0
    LFO_SPD2 = 1
    LFO_SPD3 = 2
    LFO_DEP1 = 3
    LFO_DEP2 = 4
    LFO_DEP3 = 5
    AMP_ATK = 6
    AMP_HOLD = 7
    AMP_REL = 8
    AMP_VOL = 9
    AMP_BAL = 10
    AMP_F = 11
    FX1_PARAM1 = 12
    FX1_PARAM2 = 13
    FX1_PARAM3 = 14
    FX1_PARAM4 = 15
    FX1_PARAM5 = 16
    FX1_PARAM6 = 17
    FX2_PARAM1 = 18
    FX2_PARAM2 = 19
    FX2_PARAM3 = 20
    FX2_PARAM4 = 21
    FX2_PARAM5 = 22
    FX2_PARAM6 = 23
```

Scene FX locks are stored in `SceneParams.fx1` and `SceneParams.fx2` (6 bytes each, 255 = no lock).

## Comparison: Pages and Their Implementation

| Page | Varies By | Properties | Implementation |
|------|-----------|------------|----------------|
| PLAYBACK | Machine type | Machine-specific | Machine subclasses (existing) |
| LFO | Never | Always same 6 | Direct properties in AudioPartTrack |
| AMP | Never | Always same 6 | Direct properties in AudioPartTrack |
| FX1 | FX1 type | Type-specific | Container pattern (this doc) |
| FX2 | FX2 type | Type-specific | Container pattern (this doc) |

LFO and AMP don't need containers because they're always the same structure. FX benefits from containers because the parameter meanings change based on effect type.

## Integration Points

### Existing Part Classes

```python
# In part/audio.py or part/base.py

from ..fx import _create_fx

class AudioPartTrack(BasePartTrack):

    @property
    def fx1_type(self) -> FX1Type:
        # ... existing implementation

    @property
    def fx1(self) -> BaseFX:
        return _create_fx(self, slot=1, fx_type=self.fx1_type)

    @property
    def fx2(self) -> BaseFX:
        return _create_fx(self, slot=2, fx_type=self.fx2_type)
```

### Scene Classes (to be implemented)

```python
# In scene/audio.py

from ..fx import _create_scene_fx

class AudioSceneTrack:

    @property
    def fx1(self) -> BaseSceneFX:
        part_track = self._scene._part.track(self._track_num)
        return _create_scene_fx(self, slot=1, fx_type=part_track.fx1_type)
```

## Testing Strategy

FX containers can be tested in isolation:

```python
# tests/test_fx.py

def test_filter_fx_properties():
    """Test FilterFX has correct properties."""
    # Create mock part track with FX1 set to Filter
    fx = FilterFX(mock_track, slot=1)
    fx.cutoff = 64
    assert fx.cutoff == 64

def test_filter_fx_no_delay_property():
    """Test FilterFX doesn't have delay properties."""
    fx = FilterFX(mock_track, slot=1)
    with pytest.raises(AttributeError):
        fx.delay_time

def test_scene_fx_matches_part():
    """Test scene FX type matches Part's FX type."""
    part.track(1).fx1_type = FX1Type.DELAY
    scene_fx = part.scene(1).track(1).fx1
    assert isinstance(scene_fx, DelaySceneFX)
```

## Open Questions

1. **Parameter names**: Need to document actual parameter names for each FX type from Octatrack manual/testing
2. **FX type change**: When Part's FX type changes, existing FX container references become stale - document this behavior
3. **OFF type**: How to handle `FX1Type.OFF` - return a no-op container or None?

## References

- [Octatrack Manual - Effects](https://www.elektron.se/support/?connection=octatrack-mkii#resources)
- `octapy/_io/bank.py` - Binary offsets for FX parameters
- `octapy/api/enums.py` - FX1Type, FX2Type enums
