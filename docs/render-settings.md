# Save-time and configuration helpers

Octapy applies two kinds of project-wide transformations:

1. **Eager configuration helpers** — methods on `Project` that scatter their
   effect across all banks and parts immediately when called.
2. **Save-time finalisation** — a small set of fixups keyed off
   `settings.master_track` that run inside `to_directory()` / `to_zip()`.

There is no longer a separate `RenderSettings` object; the surface is just
methods and settings on `Project`.

## Eager helper: `configure_recorder_buffer`

```python
from octapy import Project, RecordingSource

project = Project.from_template("MY PROJECT")
project.configure_recorder_buffer(7, RecordingSource.MAIN)
```

After this call, every part of every bank has track 7 set up as a Flex
machine playing its own recorder buffer, with `MAIN` as the recording
source. The change is fully applied and observable in `project` state —
no save needed.

Pass `slices=N` to additionally:

- Slice the recorder buffer into N equal pieces (writes `markers.work`).
- Enable slice mode for the recorder track in every part.
- Place N evenly-spaced trigs with `slice_index` p-locks in every pattern
  that already has activity on the other tracks.

```python
# 1. Build your patterns first
project.bank(1).pattern(1).audio_track(1).active_steps = [1, 5, 9, 13]

# 2. Then configure the recorder buffer
project.configure_recorder_buffer(7, RecordingSource.MAIN, slices=4)
```

Constraints:
- `track` must be 1–8. Cannot be 8 when `settings.master_track` is enabled.
- `slices` must be one of `{2, 4, 8, 16, 32, 64}`.
- The recorder `rlen` (default 16) must divide evenly by `slices`.
- Slice trigs are placed eagerly — call `configure_recorder_buffer` *after*
  setting pattern activity, not before.

## Save-time finalisation

When `settings.master_track = True` the save pipeline runs two narrow
fixups that have to be late-bound (they react to patterns and recorder
sources you may have set at any point):

- **Auto master trig.** For every pattern with audio activity on tracks
  1–7, a step-1 trig is added to track 8 so the master chain actually
  processes audio.
- **TRACK_8 → MAIN substitution.** Any recorder source set to `TRACK_8`
  is rewritten to `MAIN` at save time. The OT can't record track 8
  output when track 8 is the master; this lets you write `TRACK_8` as a
  logical reference and not worry about the hardware quirk.

These run automatically inside `project.to_directory()` and
`project.to_zip()`. There is no public flag or knob — they're triggered
by `master_track` alone.
