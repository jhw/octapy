# Roadmap

Features that are still genuinely not implemented in octapy's high-level API.
See [SUPPORTED.md](SUPPORTED.md) for the full coverage matrix; this file just
lists what's left.

## Out of scope (for now)

These are deliberately deferred. Binary parsing exists or could be added, but
the use case is narrow enough that we haven't built the high-level API yet.

- **Arrangements** (`arr01.work` – `arr08.work`). Full new file format: rows
  with pattern selection + repeat counts, tempo automation, MIDI transpose,
  scene/offset automation, mute masks, Loop/Jump/Halt row types. Most
  programmatic-authoring workflows don't touch arrangements; they're built
  live on the device. Resurrect if someone needs it.
- **Custom 16-step LFO designs.** Per-track custom LFO waveforms with
  interpolation masks. ot-tools-io has the byte layout
  (`CustomLfoDesign([u8; 16])`, `CustomLfoInterpolationMask([u8; 2])`); the
  octapy `_io` offsets are not defined yet.
- **Custom MIDI arp sequences.** Per-MIDI-track 16-step note sequences plus
  `arp_len` / `arp_key` setup fields. Same shape as custom LFO designs.
- **Per-sample `.ot` files (`SampleSettingsFile`).** Each `.wav` can have a
  sibling `.ot` file with trim_start/end/len, loop_start/len, loop_mode,
  stretch, quantization, gain, tempo, and 64 slices. ot-tools-io has
  `samples.rs`; octapy currently handles slot-level data via
  `markers.work` but doesn't write per-sample `.ot` files.

## Notes

If anything below is suddenly load-bearing for you, file an issue or add it
— the byte layouts are documented in ot-tools-io's Rust source.
