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

Recording setup is **per-track**. Select the track first, then access the setup pages.

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

## API Implementation Roadmap

### Low-Level API

1. **Identify byte offsets** for Recording Setup 1 & 2 parameters in bank files
2. **Map parameters** to `RecorderSetupOffset` constants:
   - INAB, INCD, RLEN, TRIG, SRC3, LOOP (Setup 1)
   - FIN, FOUT, AB_GAIN, QREC, QPL, CD_GAIN (Setup 2)
3. **Create enums** for parameter values:
   - `TrigMode`: ONE, ONE2, HOLD
   - `QRecMode`: OFF, STEP_1, STEP_4, STEP_8, PLEN
   - `InputSource`: OFF, A, B, A_PLUS_B, A_B (stereo)

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

- [ ] Exact byte offsets for recorder setup parameters in bank files
- [ ] Whether recorder setup is stored per-track or per-part
- [ ] How RLEN interacts with different time signatures and scales
- [ ] MAX value behavior for RLEN
- [ ] Recorder trig configuration (automated recording via sequencer)
