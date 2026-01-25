# Standalone Object Model Migration

## Executive Summary

Migrate octapy from a "view into bank data" architecture to a "standalone object" model inspired by pym8. This enables cleaner constructor-based configuration, better separation of concerns, and full support for reading existing OT projects.

## Current Architecture: View Model

```
Project
  └── Bank (references BankFile._data)
        └── Part (calculates offsets into BankFile._data)
              └── AudioPartTrack (reads/writes via offsets)
                    └── RecorderSetup (reads/writes via offsets)
        └── Pattern (calculates offsets into BankFile._data)
              └── AudioPatternTrack (reads/writes via offsets)
                    └── AudioStep (reads/writes via offsets)
```

**How it works:**
- All objects hold references to a shared `BankFile._data` bytearray
- Each object calculates byte offsets and reads/writes directly
- Changes are immediate - no sync/save step needed
- Objects cannot exist independently of their parent

**Limitations:**
1. **No constructor arguments** - Objects are views, not containers
   ```python
   # Current (verbose)
   track = part.track(1)
   track.machine_type = MachineType.FLEX
   track.flex_slot = 0
   track.fx1_type = FX1Type.DJ_EQ
   ```

2. **Tight coupling** - Track needs Part needs Bank needs BankFile
3. **Hard to test** - Can't create a Track in isolation
4. **Hard to clone** - Would need to deep-copy entire bank buffer

## Target Architecture: Standalone Objects

```
Project
  └── banks: List[Bank]
        └── parts: List[Part]
              └── tracks: List[AudioPartTrack]  # standalone objects
                    └── recorder: RecorderSetup  # standalone object
        └── patterns: List[Pattern]
              └── tracks: List[AudioPatternTrack]  # standalone objects
                    └── steps: List[AudioStep]  # standalone objects
```

**How it works:**
- Each object owns its own data (buffer or fields)
- Constructor accepts configuration parameters
- Reading parses binary into standalone objects
- Writing serializes objects back to binary
- Objects can exist independently

**Benefits:**
1. **Constructor arguments** - Clean, Pythonic API
   ```python
   # Target (clean)
   part.add_track(1,
       machine_type=MachineType.FLEX,
       flex_slot=0,
       fx1_type=FX1Type.DJ_EQ
   )

   # Or standalone creation
   track = AudioPartTrack(
       machine_type=MachineType.FLEX,
       flex_slot=0,
       fx1_type=FX1Type.DJ_EQ
   )
   part.set_track(1, track)
   ```

2. **Loose coupling** - Objects are independent
3. **Easy to test** - Create tracks without full project context
4. **Easy to clone** - Just copy the object

## Reference: pym8 Pattern

pym8 uses standalone objects effectively:

```python
# Creating instruments with constructor args
sampler = M8Sampler(name="kick", sample_path="/samples/kick.wav")
project.instruments[0] = sampler

# Reading existing project
project = M8Project.read_from_file("song.m8s")
sampler = project.instruments[0]
print(sampler.name)  # reads from sampler._data buffer

# Modifying and saving
sampler.cutoff = 80
project.write_to_file("song.m8s")  # serializes all objects back
```

Key implementation details:
- Each instrument has its own `_data` bytearray (215 bytes)
- Constructor applies defaults, then overrides with kwargs
- `read()` parses binary into object fields/buffer
- `write()` serializes object back to bytes

## Design Decisions

### 1. Data Storage Strategy

**Option A: Field-based storage**
```python
class AudioPartTrack:
    def __init__(self, machine_type=MachineType.FLEX, flex_slot=0, ...):
        self.machine_type = machine_type
        self.flex_slot = flex_slot
        # ... all fields as Python attributes
```
- Pros: Clean Python, easy to inspect
- Cons: Must maintain field↔offset mapping in read/write

**Option B: Buffer-based storage (like pym8)**
```python
class AudioPartTrack:
    def __init__(self, machine_type=MachineType.FLEX, flex_slot=0, ...):
        self._data = bytearray(TRACK_SIZE)
        self._apply_defaults()
        if machine_type is not None:
            self.machine_type = machine_type
        # ... properties read/write to self._data
```
- Pros: Simpler read/write, buffer is the source of truth
- Cons: Properties still needed for access

**Recommendation: Option B (buffer-based)**
- Matches pym8 pattern
- Simpler read() - just copy bytes
- Simpler write() - just return bytes
- Properties provide typed access

### 2. Constructor Signature

**Required parameters:** None - all have sensible defaults
**Optional parameters:** Any settable property

```python
class AudioPartTrack:
    def __init__(
        self,
        # Machine configuration
        machine_type: MachineType = MachineType.FLEX,
        flex_slot: int = 0,
        static_slot: int = 0,
        recorder_slot: int = 0,
        # FX configuration
        fx1_type: int = FX1Type.FILTER,
        fx2_type: int = FX2Type.DELAY,
        # AMP page
        attack: int = 0,
        hold: int = 127,
        release: int = 24,
        amp_volume: int = 108,
        balance: int = 64,
        # Volume
        main_volume: int = 108,
        cue_volume: int = 108,
    ):
```

### 3. Collection Management

Parts should manage tracks as a list/dict:

```python
class Part:
    def __init__(self):
        self._tracks: List[AudioPartTrack] = [
            AudioPartTrack() for _ in range(8)
        ]

    def track(self, num: int) -> AudioPartTrack:
        return self._tracks[num - 1]

    def set_track(self, num: int, track: AudioPartTrack):
        self._tracks[num - 1] = track
```

### 4. Read/Write Flow

**Reading:**
```
Binary File → BankFile.read() → Bank.read() → Part.read() → AudioPartTrack.read()
                                                            ↓
                                                   Creates standalone object
                                                   with data copied to _data
```

**Writing:**
```
Project.write() → Bank.write() → Part.write() → AudioPartTrack.write()
                                                         ↓
                                                 Returns bytes from _data
                     ↓
            Assembles into BankFile buffer
```

### 5. Backward Compatibility

During migration, support both patterns:

```python
# New pattern (standalone)
track = AudioPartTrack(machine_type=MachineType.FLEX, flex_slot=0)
part.set_track(1, track)

# Legacy pattern (still works via property setters)
track = part.track(1)
track.machine_type = MachineType.FLEX
track.flex_slot = 0
```

## Migration Phases

### Phase 1: Foundation (Leaf Objects)

Convert leaf objects that don't contain other objects:

1. **AudioStep** - Pattern step with trigs and p-locks
2. **RecorderSetup** - Recorder buffer configuration
3. **MidiStep** - MIDI pattern step

Each gets:
- Own `_data` buffer
- Constructor with kwargs for all properties
- `read(data)` class method
- `write()` method returning bytes
- `to_dict()` / `from_dict()` methods

**Example:**
```python
class RecorderSetup:
    def __init__(
        self,
        source: RecordingSource = RecordingSource.TRACK_1,
        rlen: int = 15,  # displays as 16
        trig: int = 0,
        loop: int = 0,
        ...
    ):
        self._data = bytearray(RECORDER_SETUP_SIZE)
        self._apply_defaults()
        if source is not None:
            self.source = source
        if rlen is not None:
            self.rlen = rlen
        ...

    @classmethod
    def read(cls, data: bytes) -> "RecorderSetup":
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:RECORDER_SETUP_SIZE])
        return instance

    def write(self) -> bytes:
        return bytes(self._data)
```

### Phase 2: Track Objects

Convert track-level objects:

1. **AudioPartTrack** - Machine configuration (contains RecorderSetup)
2. **FlexPartTrack**, **StaticPartTrack**, etc. - Machine-specific views
3. **AudioPatternTrack** - Step sequence (contains AudioSteps)
4. **MidiPartTrack** - MIDI configuration
5. **MidiPatternTrack** - MIDI step sequence

### Phase 3: Container Objects

Convert container objects:

1. **Part** - Contains 8 AudioPartTracks + 8 MidiPartTracks + 16 Scenes
2. **Pattern** - Contains 8 AudioPatternTracks + 8 MidiPatternTracks
3. **Scene** - Contains scene locks for 8 tracks

### Phase 4: Top-Level Objects

Convert top-level objects:

1. **Bank** - Contains 4 Parts + 16 Patterns
2. **Project** - Contains 16 Banks + settings + samples

### Phase 5: Read Support

Implement reading existing OT projects:

```python
# Load existing project from OT
project = Project.from_directory("/Volumes/OCTATRACK/Sets/MY SET")

# Inspect it
print(project.to_dict(include_steps=True))

# Modify it
track = project.bank(1).part(1).track(1)
track.fx1_type = FX1Type.CHORUS

# Save back
project.to_directory("/Volumes/OCTATRACK/Sets/MY SET")
```

### Phase 6: Cleanup

1. Remove legacy view-based code
2. Update all demos to use constructor pattern
3. Update documentation
4. Add comprehensive tests for read/write round-trips

## Testing Strategy

Each phase includes:

1. **Unit tests** - Object creation, property access, defaults
2. **Serialization tests** - write() produces correct bytes
3. **Round-trip tests** - read(write(obj)) == obj
4. **Integration tests** - Full project read/modify/write cycle

**Critical test:** Load a real OT project, save it, verify byte-for-byte identical (for unmodified data).

## API Examples (Target State)

### Creating a new project

```python
from octapy import Project, Part, AudioPartTrack, Pattern, MachineType, FX1Type

# Create project
project = Project.from_template("MY PROJECT")

# Configure part with constructor args
track1 = AudioPartTrack(
    machine_type=MachineType.FLEX,
    flex_slot=0,
    fx1_type=FX1Type.DJ_EQ,
    attack=0,
    hold=127,
    release=24,
)

track2 = AudioPartTrack(
    machine_type=MachineType.FLEX,
    flex_slot=1,
    fx1_type=FX1Type.FILTER,
)

# Set tracks on part
part = project.bank(1).part(1)
part.set_track(1, track1)
part.set_track(2, track2)

# Save
project.to_zip("my_project.zip")
```

### Reading existing project

```python
# Load from Octatrack
project = Project.from_directory("/Volumes/OCTATRACK/Sets/MY SET")

# Inspect
for bank_num in range(1, 17):
    bank = project.bank(bank_num)
    for part_num in range(1, 5):
        part = bank.part(part_num)
        for track_num in range(1, 9):
            track = part.track(track_num)
            if track.machine_type != MachineType.STATIC:
                print(f"Bank {bank_num} Part {part_num} Track {track_num}: {track.machine_type.name}")

# Export to JSON
import json
print(json.dumps(project.to_dict(include_steps=True), indent=2))
```

### Cloning and modifying

```python
# Clone a track
original = part.track(1)
clone = original.clone()
clone.fx1_type = FX1Type.CHORUS
part.set_track(2, clone)

# Clone a part
part2 = part.clone()
bank.set_part(2, part2)
```

## File Organization

```
octapy/
├── _io/                    # Low-level binary I/O (unchanged)
│   ├── bank.py            # BankFile, offsets, sizes
│   └── ...
├── api/
│   ├── objects/           # NEW: Standalone object implementations
│   │   ├── __init__.py
│   │   ├── step.py        # AudioStep, MidiStep
│   │   ├── track.py       # AudioPartTrack, AudioPatternTrack, etc.
│   │   ├── part.py        # Part
│   │   ├── pattern.py     # Pattern
│   │   ├── scene.py       # Scene
│   │   └── bank.py        # Bank
│   ├── project.py         # Project (updated to use objects/)
│   └── enums.py           # Enums (unchanged)
```

## Success Criteria

1. **Constructor pattern works** - All commonly-set properties configurable via kwargs
2. **Read existing projects** - Load any OT project, inspect via to_dict()
3. **Round-trip integrity** - Load → save produces identical file (for unmodified data)
4. **Demo simplified** - flex_live.py uses constructor pattern
5. **All tests pass** - Including new serialization tests
6. **Performance acceptable** - No significant slowdown for large projects
