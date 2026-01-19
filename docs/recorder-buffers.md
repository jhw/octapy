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
- Recorder buffers are sample slots 129-136 (buffer 1 = slot 129, buffer 2 = slot 130, etc.)
- Example: Track 2 can play back audio recorded on track 1 by setting `recorder_slot = 129`

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
7. Audio is in the track's recorder buffer (slot 129-136)

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
   - `QRecMode`: OFF (255), PLEN (?), STEP_1 (1), STEP_4 (4), STEP_8 (8)
   - `InputSource`: OFF (0), A_PLUS_B (1), A (2), B (3), A_B (4) - needs verification

### High-Level API

1. **RecorderSetup class** per track:
   ```python
   recorder = part.track(1).recorder
   recorder.rlen = 16
   recorder.trig = TrigMode.ONE
   recorder.qrec = QRecMode.PLEN
   recorder.src3 = 3  # Record track 3
   recorder.inab = InputSource.OFF
   ```

2. **Convenience methods**:
   ```python
   # Configure for one-shot internal recording
   recorder.setup_internal_recording(
       source_track=3,
       length=16,
       quantize=QRecMode.PLEN
   )

   # Configure for one-shot external recording
   recorder.setup_external_recording(
       input_pair="AB",
       input_mode=InputSource.A_PLUS_B,
       length=16,
       quantize=QRecMode.PLEN
   )
   ```

3. **Playback binding** (already partially implemented):
   ```python
   # Track 2 plays back recorder buffer 1
   track2 = part.track(2)
   track2.machine_type = MachineType.FLEX
   track2.recorder_slot = 129  # Buffer 1
   ```

### Project-Level API

1. **add_recorder_slots()** already exists - adds slots 129-136 to project
2. Consider **recorder buffer length** in markers.work (sample length metadata)

### To Investigate

- [x] Exact byte offsets for recorder setup parameters in bank files - **DONE** (see Binary Structure section)
- [x] Whether recorder setup is stored per-track or per-part - **Per-Part** (8 tracks × 12 bytes at PartOffset.RECORDER_SETUP)
- [ ] Verify QREC enum values (what is PLEN's numeric value?)
- [ ] Verify InputSource enum values (in_ab/in_cd settings)
- [ ] How RLEN interacts with different time signatures and scales
- [ ] RLEN value 64 = MAX behavior (records for maximum available time)
- [ ] Recorder trig configuration (automated recording via sequencer trigs)
