#!/usr/bin/env python3
"""
Create an Octatrack project with Flex machines and randomized samples.

This demo generates a project from scratch using the embedded template,
using the octapy library.

Configuration:
- 4 Parts, each with different randomly selected samples
- Track 1: Kick drum (random from kicks)
- Track 2: Snare/clap (random from snares)
- Track 3: Open hat (random from hats)
- Track 4: Closed hat (random from hats)
- Hi-hat pattern: beat on every step, randomly assigned to track 3 or 4

Samples are scanned from the Erica Pico folder and categorized by filename:
- Kicks: kk, kick, kik, BD, bass
- Snares: sn, RM, SD, cl
- Hats: HH, oh, ch, perc

Output is a zip file that can be copied to the Octatrack using copy_project.py.
"""

import argparse
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from octapy import Project, MachineType

# Constants
OUTPUT_DIR = Path(__file__).parent.parent / "tmp"
PICO_SAMPLES_DIR = OUTPUT_DIR / "Erica Pico"

# Sample categorization patterns (case insensitive)
KICK_PATTERNS = re.compile(r'(kk|kick|kik|bd|bass)', re.IGNORECASE)
SNARE_PATTERNS = re.compile(r'(sn|rm|sd|cl)', re.IGNORECASE)
HAT_PATTERNS = re.compile(r'(hh|oh|ch|perc)', re.IGNORECASE)


def scan_samples(samples_dir: Path) -> Dict[str, List[Path]]:
    """
    Recursively scan directory for WAV samples and categorize them.

    Args:
        samples_dir: Path to the samples directory

    Returns:
        Dict with keys 'kick', 'snare', 'hat' mapping to lists of sample paths
    """
    categories = {
        'kick': [],
        'snare': [],
        'hat': [],
    }

    if not samples_dir.exists():
        return categories

    for wav_file in samples_dir.rglob('*.wav'):
        filename = wav_file.name

        if KICK_PATTERNS.search(filename):
            categories['kick'].append(wav_file)
        elif SNARE_PATTERNS.search(filename):
            categories['snare'].append(wav_file)
        elif HAT_PATTERNS.search(filename):
            categories['hat'].append(wav_file)

    return categories


def path_to_ot_relative(sample_path: Path) -> str:
    """
    Convert local sample path to Octatrack-relative path.

    Local: tmp/Erica Pico/subdir/sample.wav
    OT:    ../AUDIO/Erica Pico/subdir/sample.wav
    """
    try:
        relative = sample_path.relative_to(PICO_SAMPLES_DIR)
        return f"../AUDIO/Erica Pico/{relative}"
    except ValueError:
        return str(sample_path)


def generate_hat_pattern() -> Tuple[List[int], List[int]]:
    """
    Generate randomized hat pattern with a beat on every step.

    Each step is randomly assigned to either track 3 (open hat) or track 4 (closed hat).

    Returns:
        Tuple of (open_hat_steps, closed_hat_steps)
    """
    open_hat_steps = []
    closed_hat_steps = []

    for step in range(1, 17):
        if random.random() < 0.5:
            open_hat_steps.append(step)
        else:
            closed_hat_steps.append(step)

    return open_hat_steps, closed_hat_steps


def select_samples_for_part(categories: Dict[str, List[Path]]) -> Dict[str, Path]:
    """
    Randomly select one sample from each category for a part.

    Args:
        categories: Dict mapping category names to lists of sample paths

    Returns:
        Dict mapping category names to selected sample paths
    """
    selected = {}

    for category, samples in categories.items():
        if samples:
            selected[category] = random.choice(samples)

    return selected


def create_project(name: str, output_dir: Path) -> Path:
    """
    Create a complete Octatrack project with Flex machines.

    Sets up 4 parts, each with different randomly selected samples
    and different hi-hat patterns.

    Args:
        name: Project name (will be uppercased)
        output_dir: Directory to save the output zip file

    Returns:
        Path to the created zip file
    """
    # Scan for samples in local tmp directory
    print(f"Scanning for samples in {PICO_SAMPLES_DIR}")

    if not PICO_SAMPLES_DIR.exists():
        print(f"Error: Erica Pico samples directory not found at {PICO_SAMPLES_DIR}")
        print("Please download the Erica Pico samples to tmp/Erica Pico/")
        sys.exit(1)

    categories = scan_samples(PICO_SAMPLES_DIR)

    # Check we have samples in each category
    for cat_name, samples in categories.items():
        print(f"  - Found {len(samples)} {cat_name} samples")
        if not samples:
            print(f"Error: No {cat_name} samples found.")
            print("Please ensure the Erica Pico folder contains properly named samples.")
            sys.exit(1)

    # Create project from template
    print(f"\nCreating project '{name}'")
    print("  - Using embedded template (OS 1.40B)")
    project = Project.from_template(name)

    # Get bank 1 for pattern/part configuration
    bank = project.bank(1)

    # Configure 4 parts with different samples and patterns
    print(f"\nConfiguring patterns and parts")
    for part_num in range(1, 5):
        print(f"\n  Part {part_num}:")

        # Select random samples for this part
        selected = select_samples_for_part(categories)

        # Generate hat pattern for this part
        open_hat_steps, closed_hat_steps = generate_hat_pattern()

        # Get the Part and Pattern
        part = bank.part(part_num)
        pattern = bank.pattern(part_num)

        # Track configurations for this part: (track, category, steps)
        track_configs = [
            (1, 'kick', [1, 5, 9, 13]),           # Kick on beats
            (2, 'snare', [5, 13]),                # Snare on backbeats
            (3, 'hat', open_hat_steps),           # Open hat (randomized)
            (4, 'hat', closed_hat_steps),         # Closed hat (randomized)
        ]

        print(f"    - Hat pattern: track 3 = {open_hat_steps}")
        print(f"                   track 4 = {closed_hat_steps}")

        for track_num, category, steps in track_configs:
            sample_path = selected[category]
            relative_path = path_to_ot_relative(sample_path)
            sample_name = sample_path.name

            # Add sample to project (auto-assigns slot, reuses if same path)
            # flex_count is auto-updated in all banks
            project.add_sample(
                path=relative_path,
                wav_path=sample_path,
                slot_type="FLEX",
            )
            slot = project.get_slot(relative_path)

            print(f"    - Track {track_num}: {category} ({sample_name}) -> slot {slot}")

            # Configure the track in the Part
            track = part.track(track_num)
            track.machine_type = MachineType.FLEX
            track.flex_slot = slot - 1  # 0-indexed

            # Set trigger pattern for this track
            pattern.track(track_num).active_steps = steps

        # Assign pattern to this part
        pattern.part = part_num
        print(f"    - Pattern {part_num} assigned to Part {part_num}")

    print(f"\n  Total flex slots used: {project.flex_slot_count}")

    # Save project as zip
    zip_path = output_dir / f"{name}.zip"
    print(f"\nSaving project to {zip_path}")
    project.to_zip(zip_path)

    print(f"\nProject created: {zip_path}")
    print("\nTo copy to Octatrack, run:")
    print(f"  python tools/copy_project.py '{name}'")

    return zip_path


def main():
    parser = argparse.ArgumentParser(
        description="Create an Octatrack project with randomized Flex machines"
    )
    parser.add_argument(
        "name",
        nargs="?",
        default="HELLO FLEX",
        help="Project name (default: 'HELLO FLEX')"
    )
    parser.add_argument(
        "-o", "--output",
        default=str(OUTPUT_DIR),
        help=f"Output directory for zip file (default: {OUTPUT_DIR})"
    )

    args = parser.parse_args()

    # Normalize project name to uppercase
    name = args.name.upper()

    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    create_project(name, output_dir)


if __name__ == "__main__":
    main()
