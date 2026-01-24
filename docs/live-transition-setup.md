# Octatrack Live Transition Setup

This document describes a common Octatrack live performance pattern using recorder buffers for seamless transitions between songs/patterns.

## Overview

The "transition trick" (often attributed to Tarekith) allows you to:
1. Capture the current mix to a recorder buffer
2. Crossfade to the captured audio while changing patterns/banks
3. Crossfade back to the new live content

This enables seamless transitions without audible gaps or abrupt changes.

## Octapy Integration

Octapy can automatically configure this setup via the `transition_track` render setting:

```python
project = Project.from_template("MY PROJECT")
project.settings.master_track = True
project.render_settings.transition_track = True
```

When `transition_track` is enabled, octapy automatically configures **all Parts in all Banks** with:
- T7 as Flex machine playing recorder buffer 7
- T7 recorder source set to Main
- Scene 1: T1-6 amp_volume=127, T7 amp_volume=0 (normal playback)
- Scene 2: T1-6 amp_volume=0, T7 amp_volume=127 (transition playback)

This ensures consistent transition behavior across all Parts and Banks, which is critical because:
1. Recorder buffers are global (shared across all banks)
2. When you switch banks, T7 continues playing if configured identically
3. Part changes don't affect the transition capability

## Track Allocation

| Track | Role | Machine Type |
|-------|------|--------------|
| T1-T6 | Content tracks | Any (Static, Flex, Thru, etc.) |
| T7 | Transition buffer playback | Flex (plays recorder buffer 7) |
| T8 | Master track | Master |

Note: Some performers use T4 as the transition track instead of T7. The principle is identical.

## Configuration

### T7 Recorder Setup

Configure T7's recorder to capture the master output:

**Recording Setup 1 (FUNC + REC1):**
- INAB = Off
- INCD = Off
- RLEN = 64 (or pattern length)
- TRIG = ONE (one-shot)
- SRC3 = T8 (or MAIN)
- LOOP = Off (or On for continuous capture)

**Recording Setup 2 (FUNC + REC2):**
- QREC = PLEN (quantize to pattern start)
- Other parameters as needed

### T7 Flex Machine Setup

T7's Flex machine should play its own recorder buffer:

```
Machine Type: Flex
Slot: Recorder Buffer 7 (internal slot 135)
```

In octapy:
```python
track7 = part.track(7)
track7.machine_type = MachineType.FLEX
track7.recorder_slot = 6  # Buffer 7 (0-indexed)
```

### Scene Configuration

Use XVOL on the AMP page to crossfade between content and transition tracks.

**Scene A (Normal playback):**
- T1-T6: XVOL = MAX (127)
- T7: XVOL = MIN (0)

**Scene B (Transition playback):**
- T1-T6: XVOL = MIN (0)
- T7: XVOL = MAX (127)

Copy these scene settings across all Parts to maintain consistency.

## Workflow

### Basic Transition

1. **Capture**: Record T8 (master) onto T7's buffer
   - Press REC3 on T7 (or use recorder trig)
   - Recording captures RLEN steps of the master output

2. **Engage**: Move crossfader toward Scene B
   - T1-T6 fade out via XVOL
   - T7 fades in, playing the captured audio
   - Audio continues without interruption

3. **Change**: While Scene B is engaged
   - Change patterns, banks, or even projects on T1-T6
   - Preview changes in CUE if desired
   - The audience hears only T7 (the captured loop)

4. **Disengage**: Move crossfader back toward Scene A
   - T7 fades out
   - T1-T6 fade in with new content
   - Seamless transition complete

### Important Considerations

**Reset effects before transitions:**
Any effects, filters, or parameters on T7 must be reset to neutral before the next transition. Otherwise, the captured audio will be processed through stale effect settings.

Solution: P-lock step 1 of T7 to default/neutral values across all patterns.

**Consistent setup across patterns:**
Keep T7's recorder and Flex machine configuration identical across all patterns and banks. This ensures the transition track behaves predictably regardless of where you are in your set.

**Global settings:**
- "Silence tracks" should be OFF so loops carry between patterns
- "Starts silent" should NOT be enabled for T7

## Variations

### Cue-Based Recording

Instead of recording T8/Main, record from CUE:
- Set SRC3 = CUE
- Selectively route tracks to CUE before recording
- Allows capturing specific elements rather than the full mix

### Multiple Transition Tracks

For more complex sets, dedicate two tracks to transitions:
- T6: Transition buffer A
- T7: Transition buffer B
- Allows overlapping transitions or A/B comparison

### Mangling the Transition

While Scene B is engaged, you can:
- Apply effects to T7
- Slice and rearrange the captured audio
- Resample T7 back to another buffer
- Create entirely new content from the captured loop

## References

- [Quick transition trick/live sampling questions](https://www.elektronauts.com/t/quick-transition-trick-live-sampling-questions/56138)
- [Resampling and rearranging the master track](https://www.elektronauts.com/t/resampling-and-rearranging-the-master-track/33802)
- [Recorder buffers for looping and live sampling](https://www.elektronauts.com/t/recorder-buffers-for-looping-and-live-sampling/52853)
- [Octatrack Livesets](https://www.elektronauts.com/t/octatrack-livesets/29729/11)
- [Crossfader Transition Question for Live Performance](https://www.elektronauts.com/t/crossfader-transition-question-for-live-performance-t8-xvol-scene/41469)
