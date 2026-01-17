#!/usr/bin/env python3
"""
Create an Octatrack project with Flex machines using mixed pattern sources.

Configuration:
- Banks 1-2 with all 4 parts and all 16 patterns populated each
- Each part has unique random samples on tracks 1-4
- Even patterns (0,2,4,...) use Euclidean rhythms with velocity p-locks
- Odd patterns (1,3,5,...) use Acid Banger 909 patterns with velocity+probability p-locks

Track layout per part:
- Track 1: Kick drum
- Track 2: Snare/clap
- Track 3: Hat (open or closed depending on pattern)
- Track 4: Hat (only used for 'offbeats' pattern in Acid Banger)

Pattern sources:
- Acid Banger 909: https://github.com/vitling/acid-banger
- Euclidean rhythms: Bjorklund algorithm, Toussaint's research

Samples are scanned from tmp/Erica Pico/default/ and bundled with the project.
Output is a zip file that can be copied to the Octatrack using copy_project.py.
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Tuple

from octapy import Project, MachineType, SamplePool, SampleDuration

# Import pattern generators
from patterns.acid_909 import (
    get_random_kick_pattern,
    get_random_snare_pattern,
    get_random_hat_pattern,
)
from patterns.euclid import get_random_euclidean_pattern

# Constants
OUTPUT_DIR = Path(__file__).parent.parent / "tmp"
SAMPLES_DIR = OUTPUT_DIR / "Erica Pico" / "default"

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


def configure_pattern_track(pattern, track_num: int, steps_with_volume: List[Tuple[int, int]],
                            use_probability: bool = True):
    """Configure a pattern track with steps and p-locks.

    Args:
        pattern: Pattern instance
        track_num: Track number (1-8)
        steps_with_volume: List of (step_num, volume) tuples
        use_probability: If True, also set probability p-locks (for Acid Banger)
    """
    step_nums = [s[0] for s in steps_with_volume]
    pattern.track(track_num).active_steps = step_nums

    # Add p-locks for volume (and optionally probability)
    for step_num, volume in steps_with_volume:
        step = pattern.track(track_num).step(step_num)
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
        pools: Dict with 'kicks', 'snares', 'open_hats', 'closed_hats' SamplePools
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
        open_hat_sample = pools['open_hats'].random()
        closed_hat_sample = pools['closed_hats'].random()

        # Add samples and configure tracks
        kick_slot = project.add_sample(kick_sample)
        snare_slot = project.add_sample(snare_sample)
        open_hat_slot = project.add_sample(open_hat_sample)
        closed_hat_slot = project.add_sample(closed_hat_sample)

        print(f"    Part {part_num}: {kick_sample.name}, {snare_sample.name}, {open_hat_sample.name}, {closed_hat_sample.name}")

        # Configure machine types and slots for tracks 1-4
        for track_num, slot in [(1, kick_slot), (2, snare_slot),
                                 (3, open_hat_slot), (4, closed_hat_slot)]:
            part.track(track_num).machine_type = MachineType.FLEX
            part.track(track_num).flex_slot = slot - 1

    # Configure all 16 patterns
    # Even 0-indexed (1,3,5,... in UI) = Euclid, Odd 0-indexed (2,4,6,... in UI) = Acid Banger
    print(f"\n  Bank {bank_num} ({bank_letter}) Patterns 1-16:")
    for pattern_num in range(1, 17):
        pattern = bank.pattern(pattern_num)

        # Assign to a random part (1-4)
        part_num = rng.randint(1, 4)
        pattern.part = part_num

        # 0-indexed pattern number for even/odd check
        pattern_idx = pattern_num - 1
        use_euclid = (pattern_idx % 2 == 0)  # 0,2,4,... = Euclid

        if use_euclid:
            # Euclidean patterns - velocity p-locks only (no probability)
            kick_name, kick_pattern = get_random_euclidean_pattern('kick', rng)
            snare_name, snare_pattern = get_random_euclidean_pattern('snare', rng)
            hat_name, hat_pattern = get_random_euclidean_pattern('hat', rng)

            # Convert to steps
            kick_steps = pattern_to_steps(kick_pattern)
            snare_steps = pattern_to_steps(snare_pattern)
            hat_steps = pattern_to_steps(hat_pattern)

            # Configure tracks (no probability for Euclid)
            configure_pattern_track(pattern, 1, kick_steps, use_probability=False)
            configure_pattern_track(pattern, 2, snare_steps, use_probability=False)
            configure_pattern_track(pattern, 4, hat_steps, use_probability=False)

            print(f"    Pattern {pattern_num:2d}: Part {part_num}, [Euclid] kick={kick_name}, snare={snare_name}, hat={hat_name}")

        else:
            # Acid Banger patterns - velocity + probability p-locks
            kick_name, kick_pattern = get_random_kick_pattern(rng)
            snare_name, snare_pattern = get_random_snare_pattern(rng)
            hat_name, hat_patterns = get_random_hat_pattern(rng)

            # Convert to steps
            kick_steps = pattern_to_steps(kick_pattern)
            snare_steps = pattern_to_steps(snare_pattern)

            # Configure kick and snare tracks
            configure_pattern_track(pattern, 1, kick_steps, use_probability=True)
            configure_pattern_track(pattern, 2, snare_steps, use_probability=True)

            # Configure hat tracks based on pattern type
            if hat_name == "closed":
                hat_steps = pattern_to_steps(hat_patterns)
                configure_pattern_track(pattern, 4, hat_steps, use_probability=True)
                hat_desc = f"hat_closed (T4)"
            else:
                oh_pattern, ch_pattern = hat_patterns
                oh_steps = pattern_to_steps(oh_pattern)
                ch_steps = pattern_to_steps(ch_pattern)
                configure_pattern_track(pattern, 3, oh_steps, use_probability=True)
                configure_pattern_track(pattern, 4, ch_steps, use_probability=True)
                hat_desc = f"hat_offbeats (T3+T4)"

            print(f"    Pattern {pattern_num:2d}: Part {part_num}, [Acid] kick_{kick_name}, snare_{snare_name}, {hat_desc}")


def create_project(name: str, output_dir: Path) -> Path:
    """Create an Octatrack project with Flex machines."""
    print(f"Scanning for samples in {SAMPLES_DIR}")

    if not SAMPLES_DIR.exists():
        print(f"Error: Samples directory not found at {SAMPLES_DIR}")
        sys.exit(1)

    # Create sample pools with pattern matching
    pools = {
        'kicks': SamplePool(SAMPLES_DIR, r"BD\d*\.wav$"),
        'snares': SamplePool(SAMPLES_DIR, r"(SD|CL|CP)\d*\.wav$"),
        'open_hats': SamplePool(SAMPLES_DIR, r"OH\d*\.wav$"),
        'closed_hats': SamplePool(SAMPLES_DIR, r"(HH|CH)\d*\.wav$"),
    }

    for pool_name, pool in [("kick", pools['kicks']), ("snare", pools['snares']),
                            ("open hat", pools['open_hats']), ("closed hat", pools['closed_hats'])]:
        print(f"  - Found {len(pool)} {pool_name} samples")
        if not pool:
            print(f"Error: No {pool_name} samples found.")
            sys.exit(1)

    # Create RNG for pattern generation
    rng = random.Random()

    # Create project
    print(f"\nCreating project '{name}'")
    project = Project.from_template(name)
    project.tempo = 124
    project.sample_duration = SampleDuration.SIXTEENTH

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
    parser = argparse.ArgumentParser(description="Create an Octatrack project with Acid Banger 909 patterns")
    parser.add_argument("name", nargs="?", default="HELLO FLEX", help="Project name")
    parser.add_argument("-o", "--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    create_project(args.name.upper(), output_dir)


if __name__ == "__main__":
    main()
