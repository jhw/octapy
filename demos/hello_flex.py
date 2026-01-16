#!/usr/bin/env python3
"""
Create an Octatrack project with Flex machines using Acid Banger 909 patterns.

Configuration:
- Part 1 with up to 4 tracks
- Track 1: Kick drum (acid_909 kick pattern)
- Track 2: Snare/clap (acid_909 snare pattern)
- Track 3: Hat (closed or open hat depending on pattern)
- Track 4: Hat (only used for 'offbeats' pattern which needs open + closed)

Patterns from vitling's acid-banger: https://github.com/vitling/acid-banger

Samples are scanned from tmp/Erica Pico/ recursively and bundled with the project.
Output is a zip file that can be copied to the Octatrack using copy_project.py.
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Tuple

from octapy import Project, MachineType, SamplePool, SampleDuration

# Import acid_909 patterns
from acid_909 import (
    get_random_kick_pattern,
    get_random_snare_pattern,
    get_random_hat_pattern,
)

# Constants
OUTPUT_DIR = Path(__file__).parent.parent / "tmp"
SAMPLES_DIR = OUTPUT_DIR / "Erica Pico"

# Default probability for all triggered steps
DEFAULT_PROBABILITY = 0.80


def velocity_to_volume(velocity: float) -> int:
    """Convert velocity (0.0-1.0) to OT volume (0-127).

    Scales to 50-127 range to ensure audible minimum.
    """
    if velocity <= 0:
        return 0
    # Scale 0.0-1.0 to 50-127
    return int(50 + velocity * 77)


def pattern_to_steps(pattern: List[float]) -> List[Tuple[int, int]]:
    """Convert acid_909 pattern to list of (step_num, volume) tuples.

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


def configure_track(project, part, pattern, track_num: int, pool: SamplePool,
                    steps_with_volume: List[Tuple[int, int]], pattern_name: str):
    """Configure a single track with sample, steps, and p-locks."""
    sample_path = pool.random()
    slot = project.add_sample(sample_path)

    step_nums = [s[0] for s in steps_with_volume]

    print(f"  - Track {track_num} ({pattern_name}): {sample_path.name} -> slot {slot}")
    print(f"    Steps: {step_nums}")

    part.track(track_num).machine_type = MachineType.FLEX
    part.track(track_num).flex_slot = slot - 1
    pattern.track(track_num).active_steps = step_nums

    # Add p-locks for volume and probability
    for step_num, volume in steps_with_volume:
        step = pattern.track(track_num).step(step_num)
        step.volume = volume
        step.probability = DEFAULT_PROBABILITY


def create_project(name: str, output_dir: Path) -> Path:
    """Create an Octatrack project with Flex machines."""
    print(f"Scanning for samples in {SAMPLES_DIR}")

    if not SAMPLES_DIR.exists():
        print(f"Error: Samples directory not found at {SAMPLES_DIR}")
        sys.exit(1)

    # Create sample pools with pattern matching (match type suffix before .wav)
    kicks = SamplePool(SAMPLES_DIR, r"BD\d*\.wav$")
    snares = SamplePool(SAMPLES_DIR, r"(SD|CL|CP)\d*\.wav$")
    open_hats = SamplePool(SAMPLES_DIR, r"OH\d*\.wav$")
    closed_hats = SamplePool(SAMPLES_DIR, r"(HH|CH)\d*\.wav$")

    for pool_name, pool in [("kick", kicks), ("snare", snares),
                            ("open hat", open_hats), ("closed hat", closed_hats)]:
        print(f"  - Found {len(pool)} {pool_name} samples")
        if not pool:
            print(f"Error: No {pool_name} samples found.")
            sys.exit(1)

    # Create RNG for pattern generation
    rng = random.Random()

    # Generate acid_909 patterns
    kick_name, kick_pattern = get_random_kick_pattern(rng)
    snare_name, snare_pattern = get_random_snare_pattern(rng)
    hat_name, hat_patterns = get_random_hat_pattern(rng)

    # Convert patterns to step/volume tuples
    kick_steps = pattern_to_steps(kick_pattern)
    snare_steps = pattern_to_steps(snare_pattern)

    # Create project
    print(f"\nCreating project '{name}'")
    project = Project.from_template(name)
    project.tempo = 124
    project.sample_duration = SampleDuration.SIXTEENTH
    bank = project.bank(1)
    part = bank.part(1)
    pattern = bank.pattern(1)

    print(f"\nAcid Banger 909 patterns selected:")
    print(f"  - Track 1 (kick): {kick_name}")
    print(f"  - Track 2 (snare): {snare_name}")
    print(f"  - Track 3 (hat): {hat_name}")
    if hat_name == "offbeats":
        print(f"  - Track 4 (hat): {hat_name} (closed hat complement)")

    print(f"\nConfiguring Part 1:")

    # Configure kick and snare
    configure_track(project, part, pattern, 1, kicks, kick_steps, f"kick_{kick_name}")
    configure_track(project, part, pattern, 2, snares, snare_steps, f"snare_{snare_name}")

    # Configure hats based on pattern type
    if hat_name == "closed":
        # Single track - closed hat only
        hat_steps = pattern_to_steps(hat_patterns)
        configure_track(project, part, pattern, 3, closed_hats, hat_steps, "hat_closed")
    else:
        # Dual track - offbeats mode with open and closed hats
        oh_pattern, ch_pattern = hat_patterns
        oh_steps = pattern_to_steps(oh_pattern)
        ch_steps = pattern_to_steps(ch_pattern)
        configure_track(project, part, pattern, 3, open_hats, oh_steps, "hat_open")
        configure_track(project, part, pattern, 4, closed_hats, ch_steps, "hat_closed")

    pattern.part = 1

    # Save (samples are bundled automatically)
    zip_path = output_dir / f"{name}.zip"
    print(f"\nSaving project to {zip_path}")
    print(f"  - Bundling {len(project.sample_pool)} samples")
    project.to_zip(zip_path)

    print(f"\nTo copy to Octatrack, run:")
    print(f"  ./tools/copy_project.py '{name}'")

    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Create an Octatrack project with Acid Banger 909 patterns")
    parser.add_argument("name", nargs="?", default="HELLO FLEX", help="Project name")
    parser.add_argument("-o", "--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    create_project(args.name.upper(), output_dir)


if __name__ == "__main__":
    main()
