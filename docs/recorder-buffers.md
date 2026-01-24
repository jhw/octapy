# Octatrack MK2 Recorder Buffers

This document describes how recorder buffers work on the Octatrack MK2 and serves as a roadmap for implementing recorder buffer support in the octapy API.

## Overview

The Octatrack has 8 recorder buffers, one per audio track. These buffers can capture audio from external inputs or internal sources, and the captured audio can be played back via Flex machines.

### Recording vs Playback Binding

**Recording (fixed binding):**
- Track N always records to recorder buffer N
- If you arm recording on track 1, audio goes to recorder buffer 1
- This is a fixed, unchangeable mapping

**Playback (flexible binding):**
- Any track's Flex machine can play back any recorder buffer
- Internally, recorder buffers occupy slots 128-135 (0-indexed) in the flex_slots array
- The API uses `recorder_slot` with values 0-7 for buffers 1-8
- Example: Track 2 can play back audio recorded on track 1 by setting `recorder_slot = 0`

## Recording Configuration

Recording setup is **per-Part, per-track**. Each Part stores 8 RecorderSetup structures (one per track). This means switching Parts can change your recorder configuration.

Select the track first, then access the setup pages.

### Recording Setup 1 (FUNC + REC1)

| Encoder | Parameter | Description |
|---------|-----------|-------------|
| A | **INAB** | External input AB source selection (off, A, B, A+B stereo, A+B sum) |
| B | **INCD** | External input CD source selection (off, C, D, C+D stereo, C+D sum) |
| C | **RLEN** | Recording length in 1/16th steps (e.g., 16, 32, 64) or MAX |
| D | **TRIG** | Recording mode: ONE (one-shot), ONE2 (releasable), HOLD |
| E | **SRC3** | Internal source selection (which track to record internally) |
| F | **LOOP** | Loop the recording (on/off) |

### Recording Setup 2 (FUNC + REC2)

| Encoder | Parameter | Description |
|---------|-----------|-------------|
| A | **FIN** | Fade in duration (0 = no fade) |
| B | **FOUT** | Fade out duration (0 = no fade) |
| C | **AB** | Input gain for AB |
| D | **QREC** | Quantize recording start: OFF, 1, 4, 8, PLEN |
| E | **QPL** | Quantize manual playback triggering |
| F | **CD** | Input gain for CD |

### QREC Values

- **OFF**: Recording starts immediately when triggered
- **1**: Recording starts on next 1/16th step
- **4**: Recording starts on next beat (quarter note)
- **8**: Recording starts on next half-bar
- **PLEN**: Recording starts when pattern loops to beginning

## Recording Sources

The three REC buttons map to the three source parameters:

| Button | Source Parameter | Use Case |
|--------|------------------|----------|
| **REC1** | INAB | Record from external inputs A/B |
| **REC2** | INCD | Record from external inputs C/D |
| **REC3** | SRC3 | Record internal audio (track output) |

## Triggering Recording

### Default Behavior
Hold **TRACK + REC1/2/3** to start recording from the corresponding source.

### Quick Record Mode
Enable in **PROJECT → SYSTEM → PERSONALIZE → RECORD QUICK MODE**

When enabled, simply press **REC1/2/3** on the active track (no need to hold TRACK button). This allows one-handed operation.

## One-Shot Quantized Recording Workflow

### Configuration for Internal Recording

**Recording Setup 1 (FUNC + REC1):**
- INAB = off
- INCD = off
- RLEN = 16 (or desired length)
- TRIG = ONE
- SRC3 = track to record
- LOOP = off

**Recording Setup 2 (FUNC + REC2):**
- QREC = PLEN (or 4, 8 for beat/half-bar quantization)
- Other parameters as needed

### Configuration for External Recording

**Recording Setup 1 (FUNC + REC1):**
- INAB = desired input config (for REC1) OR
- INCD = desired input config (for REC2)
- RLEN = 16 (or desired length)
- TRIG = ONE
- SRC3 = off
- LOOP = off

**Recording Setup 2 (FUNC + REC2):**
- QREC = PLEN (or 4, 8)

### Recording Execution
1. Enable RECORD QUICK MODE (one-time setup)
2. Select target track
3. Press REC1/REC2/REC3 (depending on source)
4. Recording arms and waits for QREC quantization point
5. Recording runs for RLEN steps
6. Recording stops automatically
7. Audio is in the track's recorder buffer (internal slots 128-135, API uses `recorder_slot` 0-7)

## Related Settings

### QUANTIZE LIVE REC (Personalize Menu)

This is **unrelated** to audio recording. It controls sequencer trig quantization when live-recording button presses into the sequencer.

- **Enabled**: Trigs snap to nearest 1/16th step
- **Disabled**: Trigs retain micro-timing (1/384 resolution)

## Binary Structure

### Storage Location

Recorder setup is stored **per-Part** in the bank file:
- **Offset**: `PartOffset.RECORDER_SETUP = 1547` (relative to Part start)
- **Size**: 8 tracks × 12 bytes = 96 bytes total
- **Structure**: Each track has a 12-byte `RecorderSetup` block

### RecorderSetup Structure (12 bytes per track)

From `ot-tools-io/src/parts.rs`:

```
RecorderSetupSources (6 bytes) - Setup Page 1 (FUNC+REC1):
  Offset 0: in_ab   (u8)
  Offset 1: in_cd   (u8)
  Offset 2: rlen    (u8)  - 64 = MAX, 63 and lower are actual step values
  Offset 3: trig    (u8)
  Offset 4: src3    (u8)
  Offset 5: xloop   (u8)

RecorderSetupProcessing (6 bytes) - Setup Page 2 (FUNC+REC2):
  Offset 6: fin     (u8)
  Offset 7: fout    (u8)
  Offset 8: ab      (u8)  - input gain for AB
  Offset 9: qrec    (u8)  - 255 = OFF
  Offset 10: qpl    (u8)  - 255 = OFF
  Offset 11: cd     (u8)  - input gain for CD
```

### Default Values

```
Setup Page 1:
  in_ab: 1, in_cd: 1, rlen: 64 (MAX), trig: 0, src3: 0, xloop: 1

Setup Page 2:
  fin: 0, fout: 0, ab: 0, qrec: 255 (OFF), qpl: 255 (OFF), cd: 0
```

### Parameter Value Ranges

**FIN / FOUT (Fade In / Fade Out)**

These prevent clicks/pops at recording boundaries. Values are in **sequencer steps** with 1/16th step resolution:

| Raw Value | Display Value | Steps |
|-----------|---------------|-------|
| 0 | 0 | 0 |
| 1 | 0.0625 | 1/16 step |
| 2 | 0.125 | 1/8 step |
| 4 | 0.25 | 1/4 step |
| 16 | 1.0 | 1 step |
| 64 | 4.0 | 4 steps |

Formula: `display_value = raw_value / 16.0` (0-4 steps range)

Note: FOUT adds time *after* the recording stops. If RLEN=16 and FOUT=16 (1 step), total sample length is 17 steps.

### Calculating Track Offset

```python
def recorder_setup_offset(part_offset: int, track_num: int) -> int:
    """Get byte offset for a track's RecorderSetup within a Part."""
    RECORDER_SETUP_SIZE = 12
    return part_offset + PartOffset.RECORDER_SETUP + (track_num - 1) * RECORDER_SETUP_SIZE
```

## API Implementation Roadmap

### Low-Level API

1. **Add offset constants** to `_io/bank.py`:
   ```python
   RECORDER_SETUP_SIZE = 12

   class RecorderSetupOffset:
       # Setup Page 1 (Sources)
       IN_AB = 0
       IN_CD = 1
       RLEN = 2
       TRIG = 3
       SRC3 = 4
       LOOP = 5
       # Setup Page 2 (Processing)
       FIN = 6
       FOUT = 7
       AB_GAIN = 8
       QREC = 9
       QPL = 10
       CD_GAIN = 11
   ```

2. **Create enums** for parameter values:
   - `RecTrigMode`: ONE (0), ONE2 (1), HOLD (2)
   - `QRecMode`: OFF (255), PLEN (0), STEP_1 (1), STEP_4 (4), STEP_8 (8)

### High-Level API

#### Unified RecordingSource Enum

The low-level format has three separate source parameters (IN_AB, IN_CD, SRC3), but you can only record from one source at a time. The high-level API uses a single `RecordingSource` enum that abstracts over all three:

```python
class RecordingSource(IntEnum):
    """Unified recording source selection.

    Abstracts over IN_AB, IN_CD, and SRC3 low-level parameters.
    Setting this automatically zeros out the unused source parameters.
    """
    OFF = 0
    # External inputs AB (maps to IN_AB)
    INPUT_AB = 1       # A+B stereo pair
    INPUT_A = 2        # Input A only
    INPUT_B = 3        # Input B only
    # External inputs CD (maps to IN_CD)
    INPUT_CD = 4       # C+D stereo pair
    INPUT_C = 5        # Input C only
    INPUT_D = 6        # Input D only
    # Internal track sources (maps to SRC3)
    TRACK_1 = 11
    TRACK_2 = 12
    TRACK_3 = 13
    TRACK_4 = 14
    TRACK_5 = 15
    TRACK_6 = 16
    TRACK_7 = 17
    TRACK_8 = 18
    MAIN = 19          # Main output (SRC3=9, template default)
```

When setting `recorder.source`, the RecorderSetup class:
1. Parses the enum value to determine which low-level parameter to use
2. Sets the appropriate parameter (IN_AB, IN_CD, or SRC3) with the correct value
3. Zeros out the other two parameters

#### RecorderSetup Class

```python
recorder = part.track(1).recorder

# Simple source selection (recommended)
recorder.source = RecordingSource.TRACK_3    # Record from track 3
recorder.source = RecordingSource.INPUT_AB   # Record from external AB

# Other settings
recorder.rlen = 16                # Recording length (steps)
recorder.trig = RecTrigMode.ONE   # One-shot recording
recorder.qrec = QRecMode.PLEN     # Quantize to pattern start
recorder.loop = False             # Don't loop
```

#### Playback Binding

```python
# Track 2 plays back recorder buffer 1
track2 = part.track(2)
track2.machine_type = MachineType.FLEX
track2.recorder_slot = 0  # Buffer 1 (0-indexed: 0-7 for buffers 1-8)
```

Note: `flex_slot` (for sample playback) and `recorder_slot` (for recorder buffer playback)
are mutually exclusive - they write to the same underlying byte in the binary format.
Setting one clears the other.

### Project-Level API

1. **add_recorder_slots()** already exists - adds slots 129-136 to project
2. Consider **recorder buffer length** in markers.work (sample length metadata)

### Render Settings

Since recorder setup is per-Part, switching Parts changes your recorder configuration. Add a `propagate_recorder` render setting to copy recorder setup from Part 1 to Parts 2-4:

```python
project.render_settings.propagate_recorder = True
```

Implementation in `RenderSettings`:
```python
@property
def propagate_recorder(self) -> bool:
    """
    Propagate recorder setup from Part 1 to Parts 2-4 within each bank.

    When True, copies recorder settings (INAB, INCD, RLEN, TRIG, SRC3,
    LOOP, FIN, FOUT, AB/CD gain, QREC, QPL) from Part 1 to Parts 2-4
    for each track, but only if the target Part's recorder setup is
    at template defaults.

    Default is False (manual recorder configuration per Part).
    """
    return self._propagate_recorder
```

This follows the same pattern as `propagate_src`, `propagate_amp`, `propagate_fx`, and `propagate_scenes`.

### Octapy Defaults

Octapy overrides some OT template defaults to provide sensible one-shot quantized recording out of the box:

| Parameter | OT Default | Octapy Default | Reason |
|-----------|------------|----------------|--------|
| IN_AB | 1 | 0 (Off) | No external input by default |
| IN_CD | 1 | 0 (Off) | No external input by default |
| RLEN | 64 (MAX) | 16 | One bar |
| TRIG | 0 (ONE) | 0 (ONE) | Keep one-shot |
| SRC3 | 9 (MAIN) | 0 (Off) | Explicit source selection |
| LOOP | 1 (On) | 0 (Off) | One-shot workflow |
| FIN | 0 | 0 | Keep |
| FOUT | 0 | 0 | Keep |
| AB_GAIN | 0 | 0 | Keep |
| QREC | 255 (Off) | 0 (PLEN) | Quantize to pattern start |
| QPL | 255 (Off) | 255 (Off) | Keep off |
| CD_GAIN | 0 | 0 | Keep |

### To Investigate

- [x] Exact byte offsets for recorder setup parameters in bank files - **DONE** (see Binary Structure section)
- [x] Whether recorder setup is stored per-track or per-part - **Per-Part** (8 tracks × 12 bytes at PartOffset.RECORDER_SETUP)
- [x] Verify QREC enum values - **DONE** (from ot-tools-io TrigQuantizationMode: PLEN=0, OFF=255, OneStep=1, etc.)
- [x] Verify InputSource enum values - **Superseded** by unified RecordingSource enum (uses same encoding as ThruInput: OFF=0, A_PLUS_B=1, A=2, B=3, A_B=4)
- [ ] How RLEN interacts with different time signatures and scales
- [ ] RLEN value 64 = MAX behavior (records for maximum available time)
- [ ] Recorder trig configuration (automated recording via sequencer trigs)
