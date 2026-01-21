---
title: "Are Octatrack Parts a Code Smell?"
description: "Understanding the Octatrack's hierarchical structure and questioning whether Parts were the right design choice"
date: 2025-01-21
tags: [octatrack, elektron, music-technology, software-design]
---

The Elektron Octatrack is famously confusing. Forum threads overflow with questions like "what even is a Part?" and "why can't I use my scenes after switching patterns?" Beginners spend weeks just understanding the basic hierarchy before making any music.

This confusion isn't because the Octatrack is poorly documented. It's because the underlying data structure is genuinely complex—and arguably more complex than it needs to be.

In this post, I'm going to walk through the Octatrack's internal hierarchy as it actually exists in the binary files. Not the UI abstraction, but the real structure. Along the way, I'll point out gotchas that trip up both beginners and experienced users. And at the end, I'll ask a heretical question: **are Parts a design mistake?**

## The Real Hierarchy

When you create an Octatrack project, here's what actually gets stored:

```
Project
├── Settings (tempo, master track, MIDI config)
├── Sample Slots (128 Flex + 128 Static references)
└── Banks (16 banks: A through P)
    ├── Patterns (16 patterns per bank)
    │   ├── Audio Tracks 1-8 (step sequences)
    │   │   └── Steps 1-64 (triggers, p-locks)
    │   └── MIDI Tracks 1-8 (note sequences)
    │       └── Steps 1-64 (notes, CCs)
    └── Parts (4 parts per bank)
        ├── Audio Tracks 1-8 (sound design)
        │   ├── Machine Type (Flex, Static, Thru, Neighbor, Pickup)
        │   ├── Sample Slot Assignment
        │   ├── Playback Parameters (pitch, start, length, rate)
        │   ├── AMP Parameters (attack, hold, release, volume)
        │   ├── LFO Parameters (speed, depth, destination)
        │   ├── FX1 Parameters (type + 6 params)
        │   ├── FX2 Parameters (type + 6 params)
        │   └── Recorder Setup (source, length, trigger mode)
        ├── MIDI Tracks 1-8 (channel, notes, arp)
        └── Scenes (16 scenes per part)
            └── Scene Tracks 1-8 (parameter locks)
```

Take a moment to absorb this. The hierarchy runs five levels deep: Project → Bank → Part → Scene → SceneTrack. Every level contains configuration that affects the levels below it.

This is already complex. But the real confusion comes from understanding what lives where—and what that means for your workflow.

## Patterns vs Parts: The Great Confusion

The single biggest source of Octatrack confusion is the relationship between Patterns and Parts.

**Patterns** contain your step sequences. The triggers, the timing, the parameter locks on individual steps. When you program a beat, you're editing a Pattern.

**Parts** contain your sound design. The machine types, the samples, the effects, the AMP settings. When you dial in a sound, you're editing a Part.

Here's the critical insight: **Patterns and Parts are siblings, not parent-child.**

```
Bank A
├── Pattern 1  ─┐
├── Pattern 2   │
├── Pattern 3   ├── Each pattern references ONE of the 4 parts
├── Pattern 4   │
├── ...        ─┘
├── Pattern 16
│
├── Part 1  ─┐
├── Part 2   ├── Sound design lives here
├── Part 3   │
└── Part 4  ─┘
```

Each pattern has a "Part assignment" that determines which Part's sounds it uses. Pattern 1 might use Part 1. Pattern 5 might also use Part 1. Pattern 9 might use Part 3.

This means: **changing the Part assignment on a pattern completely changes how it sounds**, even though the step sequence stays identical.

And here's where the confusion deepens. When you switch patterns during playback, the Part might change too. You're not just switching sequences—you might be switching your entire machine setup, samples, and effects simultaneously.

Is this powerful? Yes. Is it intuitive? Absolutely not.

## Gotcha #1: You Have 64 Scenes Per Bank, Not 16

The Octatrack UI shows 16 scene slots. Press [SCENE A] and you see scenes 1-16. This suggests you have 16 scenes to work with.

You actually have 64.

Scenes are **nested inside Parts**. Each Part has its own set of 16 scenes. With 4 Parts per bank, that's 64 scenes per bank.

```
Bank A
├── Part 1
│   └── Scenes 1-16  (64 scene slots total)
├── Part 2
│   └── Scenes 1-16
├── Part 3
│   └── Scenes 1-16
└── Part 4
    └── Scenes 1-16
```

This has profound implications:

**Scene isolation**: The scenes you create in Part 1 don't exist in Part 2. If you spend hours crafting the perfect crossfader morph in Part 1, Scene 5, then switch to Part 2... that scene is gone. Part 2 has its own Scene 5, which is probably blank.

**No scene sharing**: You cannot use the same scene across different Parts. If you want the same scene morph available in Parts 1, 2, 3, and 4, you need to manually recreate it four times.

**Part switching loses scenes**: Mid-performance, if you switch Parts, your carefully prepared scene assignments vanish. The crossfader now morphs between Part 2's scenes, not Part 1's.

This is why experienced Octatrack users often stick to a single Part per bank and use the other three as variations. It's the only way to maintain consistent scene access.

## Gotcha #2: MIDI Has No Scenes

While we're discussing scenes, here's another surprise: **MIDI tracks don't participate in scenes at all.**

Scenes only lock audio track parameters. You can scene-lock pitch, filter cutoff, effect sends, and volume on audio tracks 1-8. But MIDI tracks 1-8? Completely excluded.

```
Scene 5 (Part 1)
├── Audio Track 1: pitch=+12, volume=100
├── Audio Track 2: fx1_send=80
├── Audio Track 3: amp_release=64
├── ...
├── Audio Track 8: filter_cutoff=32
│
├── MIDI Track 1: (nothing - scenes don't apply)
├── MIDI Track 2: (nothing)
├── ...
└── MIDI Track 8: (nothing)
```

This means the crossfader—that beautiful performance tool for morphing between scene states—does absolutely nothing for your external MIDI gear.

Want to smoothly fade between two different velocity settings on your external synth? Can't do it with scenes. Want to morph between two CC configurations? Scenes won't help.

This feels like an architectural limitation rather than a deliberate choice. The scene system was clearly designed for audio manipulation, and MIDI was bolted on separately without integration.

## Gotcha #3: The FX Copying Problem

Every Part has its own FX configuration. Track 1 in Part 1 might have a filter and delay. Track 1 in Part 2 has its own independent filter and delay settings.

This creates a workflow headache: **if you dial in perfect FX settings in one Part, you must manually copy them to the other three Parts.**

The Octatrack provides Part copying, but it's all-or-nothing. Copy Part 1 to Part 2, and you get everything: machines, samples, scenes, effects. You can't surgically copy just the FX configuration.

In practice, this leads to one of two workflows:

**Single Part approach**: Use only Part 1 per bank. Ignore Parts 2-4. This keeps your FX consistent but wastes 75% of your Part capacity.

**Upfront configuration**: Set up all four Parts identically before starting your project. Then carefully maintain parity as you make changes. One forgotten edit and your Parts drift out of sync.

Neither approach is elegant. Both are workarounds for a structural coupling problem.

## Gotcha #4: Machine Changes Ripple Everywhere

When you change a track's machine type (say, from Flex to Thru), the ripple effects are significant:

- Playback parameters change meaning (Flex has "pitch", Thru has "input gain")
- Sample assignment becomes irrelevant (Thru machines don't play samples)
- Recorder setup might need reconfiguration
- Your scenes still contain the old parameter locks (which now control different parameters)

The last point is subtle but important. Scene locks are stored as raw parameter values, not semantic meanings. If Scene 3 locks "playback parameter 1" to value 72, that meant "pitch = +7 semitones" when you had a Flex machine. Change to Thru, and that same lock now means "input select = 72" (which might not even be a valid value).

The Octatrack doesn't clear scene locks when you change machines. The data persists, but its meaning changes. This can lead to deeply confusing behavior if you're not aware of it.

## Gotcha #5: The Audio/MIDI Divide

The Octatrack treats audio and MIDI as almost completely separate systems that happen to share the same hardware.

Audio tracks (1-8) have:
- Machine types
- Sample playback
- Effects (FX1 + FX2)
- AMP envelope
- LFO modulation
- Recorder buffers
- Scene participation

MIDI tracks (1-8) have:
- Note/channel assignment
- Arpeggiator
- CC parameters
- That's basically it

No shared effects. No shared scenes. No shared LFOs. The two systems run in parallel but barely interact.

This creates awkward situations. Want to run your external synth through the Octatrack's effects? You need to route the audio back in through a Thru machine—using up one of your 8 audio tracks just to process external gear. And even then, the MIDI track controlling that synth can't scene-lock the Thru machine's parameters.

The result is that many users treat the Octatrack as two separate devices in one box: an 8-track sampler AND an 8-track MIDI sequencer. Using them together feels more like parallel play than integration.

## The Part Coupling Problem

Let's step back and look at what Parts actually bundle together:

```
Part
├── 8 Machine Types
├── 8 Sample Assignments
├── 8 Playback Configs
├── 8 AMP Configs
├── 8 LFO Configs
├── 8 FX1 Configs
├── 8 FX2 Configs
├── 8 Recorder Configs
├── 8 MIDI Configs
└── 16 Scenes
    └── 8 Scene Tracks each
```

That's a lot of stuff tied together. Change one thing, and you're changing the whole bundle.

**Want to try a different machine on track 3?** You need to either modify the current Part (affecting all patterns using it) or switch to a different Part (losing your scenes).

**Want to A/B two different FX setups?** You need two different Parts, which means duplicating everything else or accepting that your scenes won't carry over.

**Want scene 5 from Part 1 with the machines from Part 2?** Impossible. Scenes and machines are welded together inside Parts.

In software design, we'd call this **tight coupling**. Components that could be independent are instead bound together, making the system harder to modify and reason about.

## Is This a Code Smell?

In software engineering, a "code smell" is a surface indication of a deeper design problem. It doesn't mean the code is wrong, but it suggests the architecture might benefit from reconsideration.

The Octatrack's Part system exhibits several classic code smells:

**Feature Envy**: Scenes "want" to exist independently of Parts. Users constantly wish they could share scenes across Parts or access scenes without switching their entire machine setup.

**Inappropriate Intimacy**: Machines, effects, and scenes know too much about each other. Changing one component has unexpected effects on the others because they're all bundled in the same Part container.

**Shotgun Surgery**: Want to change your FX setup consistently across a project? You need to touch multiple Parts across multiple banks. A single conceptual change requires edits in many places.

**Rigid Hierarchy**: The five-level nesting (Project → Bank → Part → Scene → SceneTrack) makes certain operations awkward. Want to share a scene between banks? Copy the entire Part. Want consistent FX across all Parts? Copy each Part to the others.

These aren't just theoretical concerns. They manifest as real workflow friction that Octatrack users deal with daily.

## What If Parts Didn't Exist?

Imagine an alternative Octatrack architecture where Parts don't exist. Instead:

```
Bank
├── Patterns (16)
│   └── Steps with triggers and p-locks
│
├── Track Configs (8)
│   ├── Machine Type
│   ├── Sample Assignment
│   ├── Playback, AMP, LFO, FX settings
│   └── Recorder Setup
│
└── Scenes (64)
    └── Parameter locks for any track
```

In this model:

**One set of machines per bank**, not four. Change a machine, and it changes everywhere in that bank. Simple.

**64 independent scenes per bank**, directly accessible. No nested Part ownership. Scene 5 is scene 5, always available regardless of which patterns you're playing.

**Patterns are pure sequences**. They contain triggers and step p-locks, nothing else. No Part assignment to worry about.

This would be a much flatter hierarchy:

```
Project → Bank → (Patterns | Tracks | Scenes)
```

Three sibling collections instead of a deeply nested tree. Want to change your kick drum sound? Edit Track 1. Want to add a scene morph? Edit Scene 12. Want to sequence a different pattern? Play Pattern 7. Each concern is isolated.

## The Digitakt Evidence

Here's where it gets interesting. Elektron's newer devices have moved away from the Parts model.

The **Digitakt** (released 2017, six years after the Octatrack) has no Parts at all. Each pattern contains:
- 8 audio tracks with machine settings
- Sound parameters (filter, amp, LFO, effects)
- Step sequences

One pattern, one sound configuration. Change patterns, your sounds change with it. Want the same sounds in a different pattern? Use pattern copy or kit copy.

The **Syntakt** and **Digitone** follow similar approaches. Sound and sequence are more tightly bound at the pattern level, without the intermediate Part abstraction.

Did Elektron learn something? It's tempting to see the Digitakt's simpler architecture as a response to Octatrack complexity. Whether that's true or not, the newer device is undeniably easier to understand.

## Why Parts Might Have Made Sense (In 2011)

Before declaring Parts a mistake, let's consider why Elektron might have designed it this way.

**Hardware constraints**: The original Octatrack was designed around 2010-2011 hardware. Memory was expensive. Having four complete Part configurations that could be swapped instantly was more memory-efficient than having 16 independent sound configurations (one per pattern).

**Performance workflow**: The Octatrack was marketed to DJs and live performers. The ability to completely swap machines, samples, and effects with a single Part change enables dramatic live transitions. One button press, entire sound transformation.

**Preset mentality**: Parts function like performance presets. You set up Part 1 as your "ambient section", Part 2 as your "build", Part 3 as your "drop", Part 4 as your "breakdown". Then you switch between them during performance.

**Elektron heritage**: The Machinedrum and Monomachine (Elektron's earlier devices) had a "Kit" concept that's similar to Parts. The Octatrack followed established Elektron paradigms.

These aren't bad reasons. In the context of 2011 hardware and certain performance workflows, Parts make sense.

But we're not in 2011 anymore.

## The Octatrack 2.0 Question

If Elektron released an Octatrack Mark III tomorrow, should they eliminate Parts?

I'd argue: **not entirely, but they should be optional.**

A hybrid model might work:

**Default mode**: Flat hierarchy. Track configs and scenes live at the bank level. Patterns are pure sequences. Simple, like the Digitakt.

**Advanced mode**: Enable Parts as optional "preset snapshots." You can still define four Part configurations if you want that DJ-style "swap everything" workflow. But they're not mandatory, and scenes can optionally be global.

**Scene flexibility**: Allow scenes to be defined at either bank level (global) or Part level (snapshot-specific). User's choice.

This preserves the power-user workflow while dramatically simplifying the common case. Beginners wouldn't need to understand Parts at all until they wanted that specific capability.

## The Workaround Reality

In practice, many Octatrack users have already adopted workarounds that effectively neutralize Parts:

**"One Part" workflow**: Only use Part 1 in each bank. Ignore Parts 2-4. This gives you consistent scene access but wastes 75% of your Part capacity.

**"Identical Parts" workflow**: Set up all four Parts identically at project start. Use Part switching for variations, accepting that you'll need to manually sync any changes.

**"Part per song section" workflow**: Dedicate each Part to a specific song section. Accept that scenes are local to each section.

These workarounds are users routing around the architecture. When a significant portion of your user base develops patterns to avoid using a feature as designed, that's a signal.

## Closing Thoughts

The Octatrack remains a remarkable instrument. Its sampling capabilities, live performance features, and deep modulation options are still unmatched in many ways. Thousands of musicians make incredible music with it despite—or perhaps because of—its complexity.

But complexity isn't always depth. Sometimes complexity is just complexity.

The Part system adds significant cognitive overhead. It creates coupling between concepts that could be independent. It forces workarounds for common operations. And it's a major contributor to the Octatrack's reputation as a difficult instrument to learn.

Would the Octatrack be a better instrument without Parts? Maybe. Would it be an easier instrument to understand? Almost certainly.

Sometimes the deepest question isn't "how does this work?" but "should it work this way at all?"

---

## Resources

The insights in this post were developed while building **octapy**, a Python library for reading and writing Octatrack binary files. If you're interested in programmatically manipulating Octatrack projects—generating patterns, copying configurations, or automating tedious setup tasks—check it out.

The binary format understanding comes from **ot-tools-io**, an excellent Rust library by Mike Robeson (dijksterhuis) that reverse-engineered the Octatrack's file formats. Without this foundational work, projects like octapy wouldn't be possible.

- **octapy**: [github.com/jhw/octapy](https://github.com/jhw/octapy)
- **ot-tools-io**: [gitlab.com/ot-tools/ot-tools-io](https://gitlab.com/ot-tools/ot-tools-io)
- **Elektron Octatrack**: [elektron.se/octatrack-mkii](https://www.elektron.se/products/octatrack-mkii/)
