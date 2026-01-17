# MIDI Implementation Plan

This document outlines the phased implementation of MIDI support in octapy.

## Phase 0: Rename Audio Classes

### Overview

Rename existing Part/Pattern track classes to use `Audio` prefix for consistency with upcoming `Midi` prefixed classes.

### Renames

| Current Name | New Name |
|--------------|----------|
| `PartTrack` | `AudioPartTrack` |
| `PatternTrack` | `AudioPatternTrack` |
| `Step` | `AudioStep` |

Container classes (`Part`, `Pattern`, `Bank`, `Project`) remain unchanged — they hold both audio and MIDI data.

### Implementation Tasks

#### 1. Rename classes

Location: `octapy/api/part.py`

```python
# Before
class PartTrack:
    ...

# After
class AudioPartTrack:
    ...
```

Location: `octapy/api/pattern.py`

```python
# Before
class PatternTrack:
    ...

class Step:
    ...

# After
class AudioPatternTrack:
    ...

class AudioStep:
    ...
```

#### 2. Update internal references

- `Part.track()` returns `AudioPartTrack`
- `Pattern.track()` returns `AudioPatternTrack`
- `AudioPatternTrack.step()` returns `AudioStep`

#### 3. Update exports

Location: `octapy/__init__.py`

```python
from .api.part import AudioPartTrack
from .api.pattern import AudioPatternTrack, AudioStep
```

#### 4. Update tests

Rename all test references from `PartTrack` → `AudioPartTrack`, etc.

#### 5. Update demos

Update `hello_flex.py` and any other demos using the old names.

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/api/part.py` | Rename `PartTrack` → `AudioPartTrack` |
| `octapy/api/pattern.py` | Rename `PatternTrack` → `AudioPatternTrack`, `Step` → `AudioStep` |
| `octapy/__init__.py` | Update exports |
| `tests/test_parts.py` | Update references |
| `tests/test_patterns.py` | Update references |
| `demos/hello_flex.py` | Update if needed |

### Verification

1. Run all tests
2. Run `hello_flex.py` demo
3. Verify no import errors

---

## Phase 1: Global MIDI Settings

### Overview

Implement project-level MIDI settings for clock, transport, and program change. These are stored in `project.work` (INI text format) and control how the Octatrack syncs with external MIDI gear.

### Current State

The low-level `ProjectSettings` dataclass already defines these fields:

```python
@dataclass
class ProjectSettings:
    midi_clock_send: int = 0
    midi_clock_receive: int = 0
    midi_transport_send: int = 0
    midi_transport_receive: int = 0
    midi_program_change_send: int = 0
    midi_program_change_send_ch: int = -1
    midi_program_change_receive: int = 0
    midi_program_change_receive_ch: int = -1
```

**What works:**
- Fields are written to `project.work` on save

**What's missing:**
- Fields are not parsed on load (use defaults)
- No high-level API on Project class
- Types are int, should expose as bool where appropriate

### Settings to Implement

| Setting | File Field | Type | Default | Description |
|---------|------------|------|---------|-------------|
| `midi_clock_send` | `MIDI_CLOCK_SEND` | bool | False | Send MIDI clock to external gear |
| `midi_clock_receive` | `MIDI_CLOCK_RECEIVE` | bool | False | Sync to incoming MIDI clock |
| `midi_transport_send` | `MIDI_TRANSPORT_SEND` | bool | False | Send start/stop/continue |
| `midi_transport_receive` | `MIDI_TRANSPORT_RECEIVE` | bool | False | Respond to start/stop/continue |
| `midi_program_change_send` | `MIDI_PROGRAM_CHANGE_SEND` | bool | False | Send program changes on pattern switch |
| `midi_program_change_send_ch` | `MIDI_PROGRAM_CHANGE_SEND_CH` | int | -1 | Channel for send (-1 = disabled) |
| `midi_program_change_receive` | `MIDI_PROGRAM_CHANGE_RECEIVE` | bool | False | Switch patterns on program change |
| `midi_program_change_receive_ch` | `MIDI_PROGRAM_CHANGE_RECEIVE_CH` | int | -1 | Channel for receive (-1 = disabled) |

### Implementation Tasks

#### 1. Add parsing in `ProjectFile._parse_content()`

Location: `octapy/_io/project.py`

```python
# In SETTINGS section parsing
midi_clock_send = re.search(r'MIDI_CLOCK_SEND=(\d+)', settings_content)
if midi_clock_send:
    self.settings.midi_clock_send = int(midi_clock_send.group(1))

midi_clock_receive = re.search(r'MIDI_CLOCK_RECEIVE=(\d+)', settings_content)
if midi_clock_receive:
    self.settings.midi_clock_receive = int(midi_clock_receive.group(1))

# ... repeat for other fields
```

#### 2. Add high-level properties on Project class

Location: `octapy/api/project.py`

```python
@property
def midi_clock_send(self) -> bool:
    """Enable/disable sending MIDI clock to external gear."""
    return bool(self._project_file.settings.midi_clock_send)

@midi_clock_send.setter
def midi_clock_send(self, value: bool):
    self._project_file.settings.midi_clock_send = int(value)

@property
def midi_clock_receive(self) -> bool:
    """Enable/disable syncing to incoming MIDI clock."""
    return bool(self._project_file.settings.midi_clock_receive)

@midi_clock_receive.setter
def midi_clock_receive(self, value: bool):
    self._project_file.settings.midi_clock_receive = int(value)

# ... similar for transport and program change
```

#### 3. Add tests

Location: `tests/test_project.py`

```python
class TestMidiSettings:
    def test_midi_clock_send_default_false(self):
        project = Project.from_template("TEST")
        assert project.midi_clock_send is False

    def test_midi_clock_send_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.midi_clock_send = True
        project.to_directory(temp_dir / "TEST")

        loaded = Project.from_directory(temp_dir / "TEST")
        assert loaded.midi_clock_send is True

    # ... similar for other settings
```

#### 4. Export from package

Location: `octapy/__init__.py`

No changes needed — settings accessed via `project.midi_clock_send` etc.

### API Usage

```python
from octapy import Project

project = Project.from_template("MY PROJECT")

# Configure MIDI sync
project.midi_clock_send = True
project.midi_transport_send = True

# Configure program change
project.midi_program_change_send = True
project.midi_program_change_send_ch = 10  # Channel 10

project.to_zip("MY PROJECT.zip")
```

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/_io/project.py` | Add parsing for 8 MIDI settings |
| `octapy/api/project.py` | Add 8 properties (4 bool, 4 int/bool pairs) |
| `tests/test_project.py` | Add roundtrip tests for each setting |

### Verification

1. Create project with settings enabled
2. Copy to Octatrack
3. Verify settings appear correctly in PROJECT > MIDI > SYNC menu

---

## Phase 2: MIDI Part Configuration (MidiPartTrack)

### Overview

Implement `MidiPartTrack` class for configuring MIDI track settings at the Part level. This is analogous to `PartTrack` for audio tracks (machine type, sample slots) but for MIDI (channel, program, default note/velocity/length).

### Settings to Implement

| Property | Field | Offset | Type | Default | Description |
|----------|-------|--------|------|---------|-------------|
| `channel` | `chan` | TBD | int | 0 | MIDI channel (0-15) |
| `bank` | `bank` | TBD | int | 128 | Bank select (128 = off) |
| `program` | `prog` | TBD | int | 128 | Program change (128 = off) |
| `default_note` | `note` | TBD | int | 48 | Base note (48 = C3) |
| `default_velocity` | `vel` | TBD | int | 100 | Base velocity (0-127) |
| `default_length` | `len` | TBD | int | 6 | Base note length |

### Note Length Values

The `default_length` field uses value `6` as the default. Based on device observation, this appears to display as "1/16" in the UI (SRC page, dial C).

**TODO: Full value mapping needs device verification.**

The exact mapping between byte values (0-127?) and musical durations (1/128, 1/64, 1/32, 1/16, 1/8, etc.) is not documented in the ot-tools-io library. For now, implement with raw integer values and default of 6.

### Implementation Tasks

#### 1. Add MidiPartTrack class

Location: `octapy/api/part.py`

```python
class MidiPartTrack:
    """
    MIDI configuration for a track within a Part.

    Provides access to MIDI channel, program, and default note parameters.
    """

    def __init__(self, part: "Part", track_num: int):
        self._part = part
        self._track_num = track_num

    @property
    def channel(self) -> int:
        """MIDI channel (0-15)."""
        # TODO: implement offset calculation
        pass

    @channel.setter
    def channel(self, value: int):
        pass

    @property
    def default_length(self) -> int:
        """Default note length. Value 6 = 1/16 (believed)."""
        pass

    @default_length.setter
    def default_length(self, value: int):
        pass

    # ... similar for other properties
```

#### 2. Add midi_track() method to Part

Location: `octapy/api/part.py`

```python
class Part:
    def __init__(self, ...):
        ...
        self._midi_tracks: Dict[int, MidiPartTrack] = {}

    def midi_track(self, track_num: int) -> MidiPartTrack:
        """
        Get MIDI configuration for a track (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPartTrack instance
        """
        if track_num not in self._midi_tracks:
            self._midi_tracks[track_num] = MidiPartTrack(self, track_num)
        return self._midi_tracks[track_num]
```

#### 3. Add low-level offsets

Location: `octapy/_io/bank.py`

```python
class MidiPartOffset:
    """Offsets for MIDI track data within a Part."""
    # TODO: Determine from ot-tools-io or reverse engineering
    MIDI_TRACK_PARAMS_VALUES = ...
    MIDI_TRACK_PARAMS_SETUP = ...
```

#### 4. Add tests

Location: `tests/test_parts.py`

```python
class TestMidiPartTrack:
    def test_channel_default(self):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.channel == 0

    def test_default_length_default(self):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.default_length == 6  # 1/16

    def test_channel_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).channel = 5
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).part(1).midi_track(1).channel == 5
```

### API Usage

```python
from octapy import Project

project = Project.from_template("MY PROJECT")
part = project.bank(1).part(1)

# Configure MIDI track 1
midi_track = part.midi_track(1)
midi_track.channel = 5           # MIDI channel 6 (0-indexed)
midi_track.program = 32          # Program 33
midi_track.default_note = 60     # Middle C
midi_track.default_velocity = 100
midi_track.default_length = 6    # 1/16 (believed default)

project.to_zip("MY PROJECT.zip")
```

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/_io/bank.py` | Add `MidiPartOffset` constants |
| `octapy/api/part.py` | Add `MidiPartTrack` class, `Part.midi_track()` method |
| `tests/test_parts.py` | Add roundtrip tests for MIDI part configuration |

### Verification

1. Create project with MIDI track configured
2. Copy to Octatrack
3. Press MIDI button, select track, verify channel/program in SRC page
4. Verify default note/velocity/length values

### Deferred

- CC number assignments (Phase 4)
- Arp setup and sequences (Phase 5)

---

## Phase 3: MIDI Pattern Sequencing (MidiPatternTrack, MidiStep)

### Overview

Implement `MidiPatternTrack` and `MidiStep` classes for MIDI sequencing. This enables placing MIDI triggers on the grid and p-locking MIDI-specific parameters.

### Key Differences from Audio Tracks

MIDI and audio p-locks serve different purposes:

| Aspect | Audio Track | MIDI Track |
|--------|-------------|------------|
| **Note/Pitch** | `pitch` = transpose (64=center) | `note` = absolute MIDI note (0-127) |
| **Amplitude** | `volume` on Amp page, dial D | `velocity` on Src page, dial B |
| **Duration** | Sample has fixed length | `length` on Src page, dial C (required) |
| **Probability** | `trig_conditions` | `trig_conditions` (same system) |

Audio `len` (Src page dial C) truncates samples and is rarely used. MIDI `length` is essential because MIDI notes require explicit duration.

### Properties to Implement

#### MidiPatternTrack

| Property | Type | Description |
|----------|------|-------------|
| `active_steps` | List[int] | Step numbers with triggers (1-64) |
| `step(n)` | MidiStep | Access step n (1-64) |

#### MidiStep

| Property | Field | P-Lock Default | Description |
|----------|-------|----------------|-------------|
| `active` | trig_mask bit | — | Trigger on/off |
| `note` | `midi.note` | 255 (disabled) | MIDI note number (0-127) |
| `velocity` | `midi.vel` | 255 (disabled) | Note velocity (0-127) |
| `length` | `midi.len` | 255 (disabled) | Note duration (6 = 1/16) |
| `condition` | trig_conditions | 0 (always) | Trig condition code |
| `probability` | trig_conditions | 1.0 | Probability (0.0-1.0) |

A p-lock value of `255` means "use Part default" (from MidiPartTrack).

### Implementation Tasks

#### 1. Add MidiPatternTrack class

Location: `octapy/api/pattern.py`

```python
class MidiPatternTrack:
    """
    MIDI sequencer data for a track within a Pattern.

    Provides access to MIDI triggers and per-step p-locks.
    """

    def __init__(self, pattern: "Pattern", track_num: int):
        self._pattern = pattern
        self._track_num = track_num
        self._steps: Dict[int, MidiStep] = {}

    @property
    def active_steps(self) -> List[int]:
        """Step numbers with active triggers (1-64)."""
        # Read from midi_track_trigs.trig_masks.trigs
        pass

    @active_steps.setter
    def active_steps(self, steps: List[int]):
        pass

    def step(self, step_num: int) -> "MidiStep":
        """Get step configuration (1-64)."""
        if step_num not in self._steps:
            self._steps[step_num] = MidiStep(self, step_num)
        return self._steps[step_num]
```

#### 2. Add MidiStep class

Location: `octapy/api/pattern.py`

```python
class MidiStep:
    """
    Configuration for a single MIDI sequencer step.

    Provides access to MIDI-specific p-locks: note, velocity, length.
    """

    def __init__(self, track: MidiPatternTrack, step_num: int):
        self._track = track
        self._step_num = step_num

    @property
    def active(self) -> bool:
        """Whether this step triggers."""
        pass

    @active.setter
    def active(self, value: bool):
        pass

    @property
    def note(self) -> Optional[int]:
        """MIDI note number p-lock (0-127), or None if not set."""
        # Read from plocks[step].midi.note, 255 = None
        pass

    @note.setter
    def note(self, value: Optional[int]):
        # Write to plocks[step].midi.note, None = 255
        pass

    @property
    def velocity(self) -> Optional[int]:
        """Velocity p-lock (0-127), or None if not set."""
        pass

    @velocity.setter
    def velocity(self, value: Optional[int]):
        pass

    @property
    def length(self) -> Optional[int]:
        """Note length p-lock (6 = 1/16), or None if not set."""
        pass

    @length.setter
    def length(self, value: Optional[int]):
        pass

    @property
    def probability(self) -> float:
        """Trigger probability (0.0-1.0)."""
        # Same trig_conditions system as audio
        pass

    @probability.setter
    def probability(self, value: float):
        pass
```

#### 3. Add midi_track() method to Pattern

Location: `octapy/api/pattern.py`

```python
class Pattern:
    def __init__(self, ...):
        ...
        self._midi_tracks: Dict[int, MidiPatternTrack] = {}

    def midi_track(self, track_num: int) -> MidiPatternTrack:
        """
        Get MIDI track sequencer data (1-8).

        Args:
            track_num: Track number (1-8)

        Returns:
            MidiPatternTrack instance
        """
        if track_num not in self._midi_tracks:
            self._midi_tracks[track_num] = MidiPatternTrack(self, track_num)
        return self._midi_tracks[track_num]
```

#### 4. Add low-level offset constants

Location: `octapy/_io/bank.py`

```python
class MidiTrigOffset:
    """Offsets for MIDI trig data within Pattern."""
    # Based on ot-tools-io patterns.rs MidiTrackTrigs structure
    HEADER = 0
    TRIG_MASKS = 4
    # ... determine from ot-tools-io
```

#### 5. Add tests

Location: `tests/test_patterns.py`

```python
class TestMidiPatternTrack:
    def test_active_steps_default_empty(self):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        assert midi_track.active_steps == []

    def test_active_steps_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.bank(1).pattern(1).midi_track(1).active_steps = [1, 5, 9, 13]
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).pattern(1).midi_track(1).active_steps == [1, 5, 9, 13]


class TestMidiStep:
    def test_note_default_none(self):
        project = Project.from_template("TEST")
        step = project.bank(1).pattern(1).midi_track(1).step(1)
        assert step.note is None

    def test_note_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        midi_track.active_steps = [1]
        midi_track.step(1).note = 60  # Middle C
        midi_track.step(1).velocity = 100
        midi_track.step(1).length = 6
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        step = loaded.bank(1).pattern(1).midi_track(1).step(1)
        assert step.note == 60
        assert step.velocity == 100
        assert step.length == 6

    def test_probability_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        midi_track.active_steps = [1]
        midi_track.step(1).probability = 0.85
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).pattern(1).midi_track(1).step(1).probability == 0.85
```

### API Usage

```python
from octapy import Project

project = Project.from_template("MY PROJECT")
pattern = project.bank(1).pattern(1)

# Configure MIDI track 1 sequencer
midi_track = pattern.midi_track(1)
midi_track.active_steps = [1, 5, 9, 13]  # 4-on-the-floor

# Add p-locks
midi_track.step(1).note = 36      # C1 (kick)
midi_track.step(1).velocity = 127
midi_track.step(1).length = 6     # 1/16

midi_track.step(5).note = 38      # D1 (snare)
midi_track.step(5).velocity = 100
midi_track.step(5).probability = 0.85

project.to_zip("MY PROJECT.zip")
```

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/_io/bank.py` | Add `MidiTrigOffset` constants |
| `octapy/api/pattern.py` | Add `MidiPatternTrack`, `MidiStep` classes, `Pattern.midi_track()` |
| `tests/test_patterns.py` | Add roundtrip tests for MIDI sequencing |

### Verification

1. Create project with MIDI pattern
2. Copy to Octatrack
3. Press MIDI button, select track, verify steps appear in sequencer
4. Play pattern, verify MIDI notes trigger on correct steps
5. Check p-locked values match (note, velocity, length)

### Deferred

- Chord notes (not2, not3, not4) — Phase 3b
- Micro-timing offsets — Phase 3b
- Trig repeats — Phase 3b

---

## Phase 4: MIDI CC Assignments and Control

### Overview

Implement CC (Control Change) support for MIDI tracks. This includes configuring which CC numbers the knobs control (Setup) and the actual CC values (Values), both at Part level and as pattern p-locks.

### Data Structure

The Octatrack separates CC configuration into two layers:

| Page | Setup (CC Numbers) | Values (Current State) |
|------|-------------------|------------------------|
| CC1 | cc1, cc2, cc3, cc4 | pb, at, cc1, cc2, cc3, cc4 |
| CC2 | cc5, cc6, cc7, cc8, cc9, cc10 | cc5, cc6, cc7, cc8, cc9, cc10 |

**Setup** determines *which* CC number each knob sends.
**Values** determines *what value* is sent for that CC.

### Default CC Assignments

| Knob | Default CC# | Standard Name |
|------|-------------|---------------|
| cc1 | 7 | Volume |
| cc2 | 1 | Mod Wheel |
| cc3 | 2 | Breath |
| cc4 | 10 | Pan |
| cc5 | 71 | Filter Resonance |
| cc6 | 72 | Release Time |
| cc7 | 73 | Attack Time |
| cc8 | 74 | Filter Cutoff |
| cc9 | 75 | Decay Time |
| cc10 | 76 | Vibrato Rate |

### Properties to Implement

#### MidiPartTrack (Part Level)

**CC Number Assignments (Setup):**

| Property | Field | Default | Description |
|----------|-------|---------|-------------|
| `cc1_number` | `cc1_setup.cc1` | 7 | CC number for knob 1 |
| `cc2_number` | `cc1_setup.cc2` | 1 | CC number for knob 2 |
| `cc3_number` | `cc1_setup.cc3` | 2 | CC number for knob 3 |
| `cc4_number` | `cc1_setup.cc4` | 10 | CC number for knob 4 |
| `cc5_number` | `cc2_setup.cc5` | 71 | CC number for knob 5 |
| `cc6_number` | `cc2_setup.cc6` | 72 | CC number for knob 6 |
| `cc7_number` | `cc2_setup.cc7` | 73 | CC number for knob 7 |
| `cc8_number` | `cc2_setup.cc8` | 74 | CC number for knob 8 |
| `cc9_number` | `cc2_setup.cc9` | 75 | CC number for knob 9 |
| `cc10_number` | `cc2_setup.cc10` | 76 | CC number for knob 10 |

**CC Default Values:**

| Property | Field | Default | Description |
|----------|-------|---------|-------------|
| `pitch_bend` | `cc1_values.pb` | 64 | Pitch bend (64 = center) |
| `aftertouch` | `cc1_values.at` | 0 | Channel aftertouch |
| `cc1_value` | `cc1_values.cc1` | 127 | Default value for CC1 |
| `cc2_value` | `cc1_values.cc2` | 0 | Default value for CC2 |
| `cc3_value` | `cc1_values.cc3` | 0 | Default value for CC3 |
| `cc4_value` | `cc1_values.cc4` | 64 | Default value for CC4 |
| `cc5_value` | `cc2_values.cc5` | 0 | Default value for CC5 |
| ... | ... | 0 | ... |
| `cc10_value` | `cc2_values.cc10` | 0 | Default value for CC10 |

#### MidiStep (Pattern Level P-Locks)

| Property | Field | P-Lock Default | Description |
|----------|-------|----------------|-------------|
| `pitch_bend` | `ctrl1.pb` | 255 (disabled) | Pitch bend p-lock |
| `aftertouch` | `ctrl1.at` | 255 (disabled) | Aftertouch p-lock |
| `cc1` | `ctrl1.cc1` | 255 (disabled) | CC1 value p-lock |
| `cc2` | `ctrl1.cc2` | 255 (disabled) | CC2 value p-lock |
| `cc3` | `ctrl1.cc3` | 255 (disabled) | CC3 value p-lock |
| `cc4` | `ctrl1.cc4` | 255 (disabled) | CC4 value p-lock |
| `cc5` | `ctrl2.cc5` | 255 (disabled) | CC5 value p-lock |
| ... | ... | 255 | ... |
| `cc10` | `ctrl2.cc10` | 255 (disabled) | CC10 value p-lock |

### Implementation Tasks

#### 1. Extend MidiPartTrack with CC properties

Location: `octapy/api/part.py`

```python
class MidiPartTrack:
    # ... existing properties from Phase 2 ...

    # CC Number Assignments
    @property
    def cc1_number(self) -> int:
        """CC number assigned to knob 1 (0-127)."""
        pass

    @cc1_number.setter
    def cc1_number(self, value: int):
        pass

    # ... cc2_number through cc10_number ...

    # CC Default Values
    @property
    def pitch_bend(self) -> int:
        """Default pitch bend value (64 = center)."""
        pass

    @pitch_bend.setter
    def pitch_bend(self, value: int):
        pass

    @property
    def cc1_value(self) -> int:
        """Default value for CC1 (0-127)."""
        pass

    @cc1_value.setter
    def cc1_value(self, value: int):
        pass

    # ... cc2_value through cc10_value, aftertouch ...
```

#### 2. Extend MidiStep with CC p-locks

Location: `octapy/api/pattern.py`

```python
class MidiStep:
    # ... existing properties from Phase 3 ...

    @property
    def pitch_bend(self) -> Optional[int]:
        """Pitch bend p-lock (0-127, 64=center), or None if not set."""
        pass

    @pitch_bend.setter
    def pitch_bend(self, value: Optional[int]):
        pass

    @property
    def cc1(self) -> Optional[int]:
        """CC1 value p-lock (0-127), or None if not set."""
        pass

    @cc1.setter
    def cc1(self, value: Optional[int]):
        pass

    # ... cc2 through cc10, aftertouch ...
```

#### 3. Add tests

Location: `tests/test_parts.py` and `tests/test_patterns.py`

```python
class TestMidiPartTrackCC:
    def test_cc1_number_default(self):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).part(1).midi_track(1)
        assert midi_track.cc1_number == 7  # Volume

    def test_cc_number_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        project.bank(1).part(1).midi_track(1).cc1_number = 74  # Filter cutoff
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).part(1).midi_track(1).cc1_number == 74


class TestMidiStepCC:
    def test_cc_plock_roundtrip(self, temp_dir):
        project = Project.from_template("TEST")
        midi_track = project.bank(1).pattern(1).midi_track(1)
        midi_track.active_steps = [1]
        midi_track.step(1).cc1 = 100  # Automate CC1
        project.to_zip(temp_dir / "TEST.zip")

        loaded = Project.from_zip(temp_dir / "TEST.zip")
        assert loaded.bank(1).pattern(1).midi_track(1).step(1).cc1 == 100
```

### API Usage

```python
from octapy import Project

project = Project.from_template("MY PROJECT")
part = project.bank(1).part(1)
pattern = project.bank(1).pattern(1)

# Configure CC assignments for MIDI track 1
midi_part = part.midi_track(1)
midi_part.cc1_number = 74   # Assign knob 1 to filter cutoff
midi_part.cc2_number = 71   # Assign knob 2 to resonance
midi_part.cc1_value = 64    # Default cutoff at center

# Automate filter cutoff in pattern
midi_pattern = pattern.midi_track(1)
midi_pattern.active_steps = [1, 5, 9, 13]
midi_pattern.step(1).cc1 = 20   # Low cutoff
midi_pattern.step(5).cc1 = 80   # High cutoff
midi_pattern.step(9).cc1 = 40   # Medium cutoff
midi_pattern.step(13).cc1 = 100 # Open

project.to_zip("MY PROJECT.zip")
```

### Files to Modify

| File | Changes |
|------|---------|
| `octapy/api/part.py` | Add CC number and value properties to MidiPartTrack |
| `octapy/api/pattern.py` | Add CC p-lock properties to MidiStep |
| `tests/test_parts.py` | Add CC assignment tests |
| `tests/test_patterns.py` | Add CC p-lock tests |

### Verification

1. Create project with CC assignments configured
2. Copy to Octatrack
3. Press MIDI button, go to CC1/CC2 setup pages, verify CC numbers
4. Check CC values pages for default values
5. Play pattern, monitor MIDI output for CC automation

---

## Future Phases

- **Phase 5**: Arp sequences and advanced MIDI features
