# Unparsed project.work Fields

This document tracks fields in `project.work` that are written but not parsed when loading. These fields use default values when a project is loaded, which means modifying and re-saving an existing project could overwrite custom settings.

## Current Status

The `ProjectFile._parse_content()` method currently parses:
- `TEMPOx24` (tempo)
- `PATTERN_TEMPO_ENABLED`
- `[SAMPLE]` sections

All other fields use dataclass defaults when loading.

## Impact

**Template-based workflow (unaffected)**: Creating new projects with `Project.from_template()` works correctly since templates have appropriate defaults.

**Load-modify-save workflow (affected)**: Loading an existing project with custom settings, modifying it, and saving would overwrite unparsed fields with defaults.

## Unparsed Fields

### SETTINGS Section

#### MIDI Settings
| Field | Default | Description |
|-------|---------|-------------|
| `MIDI_CLOCK_SEND` | 0 | Send MIDI clock |
| `MIDI_CLOCK_RECEIVE` | 0 | Receive MIDI clock |
| `MIDI_TRANSPORT_SEND` | 0 | Send MIDI transport |
| `MIDI_TRANSPORT_RECEIVE` | 0 | Receive MIDI transport |
| `MIDI_PROGRAM_CHANGE_SEND` | 0 | Send program change |
| `MIDI_PROGRAM_CHANGE_SEND_CH` | -1 | Program change send channel |
| `MIDI_PROGRAM_CHANGE_RECEIVE` | 0 | Receive program change |
| `MIDI_PROGRAM_CHANGE_RECEIVE_CH` | -1 | Program change receive channel |

#### Recorder Settings
| Field | Default | Description |
|-------|---------|-------------|
| `DYNAMIC_RECORDERS` | 0 | Dynamic recorder allocation |
| `RECORD_24BIT` | 0 | Record in 24-bit |
| `RESERVED_RECORDER_COUNT` | 8 | Number of reserved recorders |
| `RESERVED_RECORDER_LENGTH` | 16 | Reserved recorder length (bars) |
| `LOAD_24BIT_FLEX` | 0 | Load 24-bit samples to flex |

#### Other Settings
| Field | Default | Description |
|-------|---------|-------------|
| `WRITEPROTECTED` | 0 | Project write protection |

### STATES Section

These track UI state (which bank/pattern/track is selected). Losing these just affects which page the OT opens to.

| Field | Default | Description |
|-------|---------|-------------|
| `BANK` | 0 | Current bank |
| `PATTERN` | 0 | Current pattern |
| `PART` | 0 | Current part |
| `TRACK` | 0 | Current track |
| `TRACK_OTHERMODE` | 0 | Track other mode |
| `ARRANGEMENT` | 0 | Current arrangement |
| `ARRANGEMENT_MODE` | 0 | Arrangement mode |
| `SCENE_A_MUTE` | 0 | Scene A mute state |
| `SCENE_B_MUTE` | 0 | Scene B mute state |
| `TRACK_CUE_MASK` | 0 | Track cue bitmask |
| `TRACK_MUTE_MASK` | 0 | Track mute bitmask |
| `TRACK_SOLO_MASK` | 0 | Track solo bitmask |
| `MIDI_MODE` | 0 | MIDI mode |
| `MIDI_TRACK_MUTE_MASK` | 0 | MIDI track mute bitmask |
| `MIDI_TRACK_SOLO_MASK` | 0 | MIDI track solo bitmask |

## Priority for Future Implementation

### High Priority
None currently - template workflow covers main use case.

### Medium Priority
- Recorder settings (if users need custom recorder configurations)
- MIDI clock/transport settings (if users sync with external gear)

### Low Priority
- UI state fields (cosmetic only)
- Other MIDI settings (rarely customized)

## Adding Parsing

To parse a new field, add to `ProjectFile._parse_content()`:

```python
# In the SETTINGS section parsing block
field_match = re.search(r'FIELD_NAME=(\d+)', settings_content)
if field_match:
    self.settings.field_name = int(field_match.group(1))
```

For STATES section, add similar parsing after creating a STATES block parser.
