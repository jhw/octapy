#!/usr/bin/env python3
"""
Create an Octatrack project with Flex machines.

Configuration:
- Part 1 with 4 tracks
- Track 1: Kick drum
- Track 2: Snare/clap
- Track 3: Open hat
- Track 4: Closed hat

Samples are scanned from tmp/Erica Pico/default/ and bundled with the project.

Output is a zip file that can be copied to the Octatrack using copy_project.py.
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Tuple

from octapy import Project, MachineType, SamplePool

# Constants
OUTPUT_DIR = Path(__file__).parent.parent / "tmp"
SAMPLES_DIR = OUTPUT_DIR / "Erica Pico" / "default"


def generate_hat_pattern() -> Tuple[List[int], List[int]]:
    """Generate randomized hat pattern with a beat on every step."""
    open_hat_steps = []
    closed_hat_steps = []
    for step in range(1, 17):
        if random.random() < 0.5:
            open_hat_steps.append(step)
        else:
            closed_hat_steps.append(step)
    return open_hat_steps, closed_hat_steps


def create_project(name: str, output_dir: Path) -> Path:
    """Create an Octatrack project with Flex machines."""
    print(f"Scanning for samples in {SAMPLES_DIR}")

    if not SAMPLES_DIR.exists():
        print(f"Error: Samples directory not found at {SAMPLES_DIR}")
        sys.exit(1)

    # Create sample pools with pattern matching (match type suffix before .wav)
    kicks = SamplePool(SAMPLES_DIR, r"BD\d*\.wav$")
    snares = SamplePool(SAMPLES_DIR, r"(SD|CL)\d*\.wav$")
    hats = SamplePool(SAMPLES_DIR, r"(HH|OH|CH)\d*\.wav$")

    for pool_name, pool in [("kick", kicks), ("snare", snares), ("hat", hats)]:
        print(f"  - Found {len(pool)} {pool_name} samples")
        if not pool:
            print(f"Error: No {pool_name} samples found.")
            sys.exit(1)

    # Create project
    print(f"\nCreating project '{name}'")
    project = Project.from_template(name)
    project.tempo = 124
    bank = project.bank(1)
    part = bank.part(1)
    pattern = bank.pattern(1)

    # Generate hat pattern
    open_hat_steps, closed_hat_steps = generate_hat_pattern()

    # Track configurations: (track, pool, steps)
    track_configs = [
        (1, kicks, [1, 5, 9, 13]),
        (2, snares, [5, 13]),
        (3, hats, open_hat_steps),
        (4, hats, closed_hat_steps),
    ]

    print(f"\nConfiguring Part 1:")
    print(f"  - Hat pattern: track 3 = {open_hat_steps}")
    print(f"                 track 4 = {closed_hat_steps}")

    for track_num, pool, steps in track_configs:
        sample_path = pool.random()
        slot = project.add_sample(sample_path)

        print(f"  - Track {track_num}: {sample_path.name} -> slot {slot}")

        part.track(track_num).machine_type = MachineType.FLEX
        part.track(track_num).flex_slot = slot - 1
        pattern.track(track_num).active_steps = steps

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
    parser = argparse.ArgumentParser(description="Create an Octatrack project with Flex machines")
    parser.add_argument("name", nargs="?", default="HELLO FLEX", help="Project name")
    parser.add_argument("-o", "--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    create_project(args.name.upper(), output_dir)


if __name__ == "__main__":
    main()
