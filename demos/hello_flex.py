#!/usr/bin/env python3
"""
Create an Octatrack project with Flex machines using Euclidean rhythm patterns.

Configuration:
- Banks 1-2 with all 4 parts and all 16 patterns populated each
- Each part has unique random samples on tracks 1-3
- All patterns use Euclidean rhythms with velocity p-locks
- Kick and hat tracks have 85% probability p-locks

Track layout per part:
- Track 1: Kick drum (with probability)
- Track 2: Snare/clap (no probability)
- Track 3: Hat (with probability)

Pattern source: Bjorklund algorithm, Toussaint's Euclidean rhythm research

Samples are scanned from tmp/Erica Pico/ and bundled with the project.
Output is a zip file that can be copied to the Octatrack using copy_project.py.
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Tuple

from octapy import Project, MachineType, SamplePool, NoteLength, FX1Type, FX2Type, RecordingSource

from patterns.euclid import get_random_euclidean_pattern

# Constants
OUTPUT_DIR = Path(__file__).parent.parent / "tmp" / "projects"
SAMPLES_DIR = Path(__file__).parent.parent / "tmp" / "samples" / "Erica Pico"

# Probability for kick and hat tracks
DEFAULT_PROBABILITY = 0.85


def velocity_to_volume(velocity: float) -> int:
    """Convert velocity (0.0-1.0) to OT volume (0-127).

    Scales to 50-127 range to ensure audible minimum.
    """
    if velocity <= 0:
        return 0
    # Scale 0.0-1.0 to 50-127
    return int(50 + velocity * 77)


def pattern_to_steps(pattern: List[float]) -> List[Tuple[int, int]]:
    """Convert pattern to list of (step_num, volume) tuples.

    Args:
        pattern: List of 16 velocity values (0.0-1.0), 0.0 = no hit

    Returns:
        List of (step_num, volume) for triggered steps (1-indexed)
    """
    steps = []
    for i, velocity in enumerate(pattern):
        if velocity > 0:
            step_num = i + 1  # 1-indexed
            volume = velocity_to_volume(velocity)
            steps.append((step_num, volume))
    return steps


def configure_pattern_track(pattern, track_num: int, steps_with_volume: List[Tuple[int, int]],
                            use_volume: bool = True, use_probability: bool = False):
    """Configure a pattern track with steps and p-locks.

    Args:
        pattern: Pattern instance
        track_num: Track number (1-8)
        steps_with_volume: List of (step_num, volume) tuples
        use_volume: If True, set volume p-locks
        use_probability: If True, set probability p-locks
    """
    step_nums = [s[0] for s in steps_with_volume]
    pattern.track(track_num).active_steps = step_nums

    # Add p-locks for volume and/or probability
    if use_volume or use_probability:
        for step_num, volume in steps_with_volume:
            step = pattern.track(track_num).step(step_num)
            if use_volume:
                step.volume = volume
            if use_probability:
                step.probability = DEFAULT_PROBABILITY

    return step_nums


def configure_bank(project, bank, bank_num: int, pools: dict, rng: random.Random):
    """Configure a bank with 4 parts and 16 patterns.

    Args:
        project: Project instance
        bank: Bank instance
        bank_num: Bank number (1-16)
        pools: Dict with 'kicks', 'snares', 'hats' SamplePools
        rng: Random number generator
    """
    bank_letter = chr(ord('A') + bank_num - 1)

    # Configure all 4 parts with unique samples
    print(f"\n  Bank {bank_num} ({bank_letter}) Parts 1-4:")
    for part_num in range(1, 5):
        part = bank.part(part_num)

        # Select random samples for this part
        kick_sample = pools['kicks'].random()
        snare_sample = pools['snares'].random()
        hat_sample = pools['hats'].random()

        # Add samples and configure tracks
        kick_slot = project.add_sample(kick_sample)
        snare_slot = project.add_sample(snare_sample)
        hat_slot = project.add_sample(hat_sample)

        print(f"    Part {part_num}: {kick_sample.name}, {snare_sample.name}, {hat_sample.name}")

        # Configure machine types and slots for tracks 1-3
        for track_num, slot in [(1, kick_slot), (2, snare_slot), (3, hat_slot)]:
            track = part.track(track_num)
            track.machine_type = MachineType.FLEX
            track.flex_slot = slot - 1
            track.apply_recommended_flex_defaults()  # length=127, length_mode=TIME
            track.fx1_type = FX1Type.DJ_EQ

        # Configure tracks 5-7 as Flex machines playing from their own recorder buffers
        # Each track's recorder buffer listens to the corresponding sample track (1-3)
        for track_num, source in [(5, RecordingSource.TRACK_1),
                                  (6, RecordingSource.TRACK_2),
                                  (7, RecordingSource.TRACK_3)]:
            track = part.track(track_num)
            track.machine_type = MachineType.FLEX
            track.recorder_slot = track_num - 1  # Track 5 uses buffer 5 (index 4), etc.
            track.apply_recommended_flex_defaults()  # length=127, length_mode=TIME
            track.recorder.source = source  # Buffer 5 listens to track 1, etc.

        # Configure FX on track 8 (master track)
        track8 = part.track(8)
        track8.fx1_type = FX1Type.SPATIALIZER
        track8.fx2_type = FX2Type.CHORUS

    # Configure all 16 patterns with Euclidean rhythms
    # All patterns default to Part 1; switch parts manually on OT to use Parts 2-4
    print(f"\n  Bank {bank_num} ({bank_letter}) Patterns 1-16:")
    for pattern_num in range(1, 17):
        pattern = bank.pattern(pattern_num)

        # Generate Euclidean patterns
        kick_name, kick_pattern = get_random_euclidean_pattern('kick', rng)
        snare_name, snare_pattern = get_random_euclidean_pattern('snare', rng)
        hat_name, hat_pattern = get_random_euclidean_pattern('hat', rng)

        # Convert to steps
        kick_steps = pattern_to_steps(kick_pattern)
        snare_steps = pattern_to_steps(snare_pattern)
        hat_steps = pattern_to_steps(hat_pattern)

        # Configure tracks:
        # - Kick (track 1): volume + probability
        # - Snare (track 2): no p-locks
        # - Hat (track 3): volume + probability
        configure_pattern_track(pattern, 1, kick_steps, use_volume=True, use_probability=True)
        configure_pattern_track(pattern, 2, snare_steps, use_volume=False, use_probability=False)
        configure_pattern_track(pattern, 3, hat_steps, use_volume=True, use_probability=True)

        print(f"    Pattern {pattern_num:2d}: kick={kick_name}, snare={snare_name}, hat={hat_name}")


def create_project(name: str, output_dir: Path) -> Path:
    """Create an Octatrack project with Flex machines."""
    print(f"Scanning for samples in {SAMPLES_DIR}")

    if not SAMPLES_DIR.exists():
        print(f"Error: Samples directory not found at {SAMPLES_DIR}")
        sys.exit(1)

    # Create sample pools with pattern matching
    pools = {
        'kicks': SamplePool(SAMPLES_DIR, r"BD|KK|KIK|BASS\d*\.wav$"),
        'snares': SamplePool(SAMPLES_DIR, r"(SD|CL|CP|HC)\d*\.wav$"),
        'hats': SamplePool(SAMPLES_DIR, r"(OH|HH|CY|PL|RS)\d*\.wav$"),
    }

    for pool_name, pool in [("kick", pools['kicks']), ("snare", pools['snares']),
                            ("hat", pools['hats'])]:
        print(f"  - Found {len(pool)} {pool_name} samples")
        if not pool:
            print(f"Error: No {pool_name} samples found.")
            sys.exit(1)

    # Create RNG for pattern generation
    rng = random.Random()

    # Create project
    print(f"\nCreating project '{name}'")
    project = Project.from_template(name)
    project.settings.tempo = 124

    # Enable master track (track 8 receives summed output of tracks 1-7)
    project.settings.master_track = True

    # Configure render settings (octapy-specific, not saved to OT files)
    # Enable propagation so all 4 parts are consistent when switching
    project.render_settings.sample_duration = NoteLength.SIXTEENTH
    project.render_settings.auto_master_trig = True
    project.render_settings.propagate_scenes = True
    project.render_settings.propagate_src = True
    project.render_settings.propagate_amp = True
    project.render_settings.propagate_fx = True
    project.render_settings.propagate_recorder = True

    # Configure Banks 1 and 2
    print(f"\nConfiguring Banks 1-2:")
    for bank_num in [1, 2]:
        bank = project.bank(bank_num)
        configure_bank(project, bank, bank_num, pools, rng)

    # Save (samples are bundled automatically)
    zip_path = output_dir / f"{name}.zip"
    print(f"\nSaving project to {zip_path}")
    print(f"  - Bundling {len(project.sample_pool)} samples")
    project.to_zip(zip_path)

    print(f"\nTo copy to Octatrack, run:")
    print(f"  ./tools/copy_project.py '{name}'")

    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Create an Octatrack project with Euclidean rhythm patterns")
    parser.add_argument("name", nargs="?", default="HELLO FLEX", help="Project name")
    parser.add_argument("-o", "--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    create_project(args.name.upper(), output_dir)


if __name__ == "__main__":
    main()
