#!/usr/bin/env python3
"""
Create a minimal Octatrack project with Flex machines.

This demo generates a project from scratch using the embedded template,
using the octapy library (pym8-style, ported from ot-tools-io Rust).

Configuration:
- Track 1: Kick drum, slot 1, steps 1, 5, 9, 13
- Track 2: Snare/clap, slot 2, steps 5, 13
- Track 3: Open hat, slot 3, randomized pattern
- Track 4: Closed hat, slot 4, randomized pattern

Hats have 80% chance per step, with 50/50 split between open and closed.

Output is a zip file that can be copied to the Octatrack using copy_project.py.
"""

import argparse
import os
import random
import shutil
import tempfile
import wave
from pathlib import Path

from octapy import BankFile, MarkersFile, ProjectFile, MachineType, zip_project, extract_template

# Constants
OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"
OUTPUT_DIR = Path(__file__).parent.parent / "tmp"

# Sample paths for each track (relative to project folder)
TRACK_SAMPLES = [
    "../AUDIO/Erica Pico/default/028008BD.wav",   # Track 1: Kick drum
    "../AUDIO/Erica Pico/default/31IBHC.wav",     # Track 2: Snare/clap
    "../AUDIO/Erica Pico/default/468008OH.wav",   # Track 3: Open hat
    "../AUDIO/Erica Pico/default/418008CH.wav",   # Track 4: Closed hat
]


def resolve_sample_path(sample_path: str) -> Path:
    """Resolve a relative sample path to an absolute path on the Octatrack."""
    if sample_path.startswith("../"):
        return Path(OCTATRACK_DEVICE) / sample_path[3:]
    return Path(OCTATRACK_DEVICE) / sample_path


def get_wav_frame_count(wav_path: Path) -> int:
    """Get the number of audio frames in a WAV file."""
    try:
        with wave.open(str(wav_path), 'rb') as w:
            return w.getnframes()
    except Exception as e:
        print(f"Warning: Could not read WAV file {wav_path}: {e}")
        return 0


def generate_hat_patterns() -> tuple:
    """
    Generate randomized hat patterns.

    80% chance of a hat on each step, 50/50 split between open and closed.

    Returns:
        Tuple of (open_hat_steps, closed_hat_steps)
    """
    open_hat_steps = []
    closed_hat_steps = []

    for step in range(1, 17):
        if random.random() < 0.8:  # 80% chance of a hat
            if random.random() < 0.5:
                open_hat_steps.append(step)
            else:
                closed_hat_steps.append(step)

    return open_hat_steps, closed_hat_steps


def create_project(name: str, output_dir: Path) -> Path:
    """
    Create a complete Octatrack project with Flex machines.

    Args:
        name: Project name (will be uppercased)
        output_dir: Directory to save the output zip file

    Returns:
        Path to the created zip file
    """
    zip_path = output_dir / f"{name}.zip"

    # Work in a temp directory
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / name

        # Extract embedded template to create project
        print(f"Creating project '{name}'")
        print("  - Using embedded template (OS 1.40B)")
        extract_template(project_dir)

        # Generate randomized hat patterns
        open_hat_steps, closed_hat_steps = generate_hat_patterns()

        # Track configurations: (track, slot, steps, sample_path)
        track_configs = [
            (1, 1, [1, 5, 9, 13], TRACK_SAMPLES[0]),      # Kick on beats
            (2, 2, [5, 13], TRACK_SAMPLES[1]),             # Snare on backbeats
            (3, 3, open_hat_steps, TRACK_SAMPLES[2]),      # Open hat (randomized)
            (4, 4, closed_hat_steps, TRACK_SAMPLES[3]),    # Closed hat (randomized)
        ]

        print(f"  - Open hat pattern: steps {open_hat_steps}")
        print(f"  - Closed hat pattern: steps {closed_hat_steps}")

        # Get sample frame counts (requires Octatrack to be mounted)
        sample_counts = {}
        for track, slot, steps, sample_path in track_configs:
            actual_path = resolve_sample_path(sample_path)
            frame_count = get_wav_frame_count(actual_path)
            sample_counts[slot] = frame_count
            sample_name = os.path.basename(sample_path)
            if frame_count > 0:
                print(f"  - Track {track} sample ({sample_name}): {frame_count} frames")
            else:
                print(f"  - Warning: Could not determine sample length for {sample_name}")

        # === Modify bank01.work ===
        bank01_path = project_dir / "bank01.work"
        print(f"Configuring bank01.work")

        bank = BankFile.from_file(bank01_path)

        # Get Part 1 (unsaved state) to configure machines
        part = bank.get_part(1)
        print(f"  - Configuring Part 1")

        for track, slot, steps, sample_path in track_configs:
            print(f"  - Track {track}: Flex machine, slot {slot}, steps {steps}")

            # Set trigger pattern for track in pattern 1
            bank.set_trigs(pattern=1, track=track, steps=steps)

            # Set machine type to Flex in Part 1
            part.set_machine_type(track=track, machine_type=MachineType.FLEX)

            # Set flex sample slot assignment in Part 1 (0-indexed internally)
            part.set_flex_slot(track=track, slot=slot - 1)

        # Assign pattern 1 to Part 1 (part_assignment 0 = Part 1)
        pattern = bank.get_pattern(1)
        pattern.part_assignment = 0
        print(f"  - Pattern 1 assigned to Part 1")

        # Set flex counter (number of active flex sample slots)
        bank.flex_count = len(track_configs)
        print(f"  - Flex counter: {bank.flex_count}")

        # Write bank file (auto-updates checksum)
        bank.to_file(bank01_path)

        # === Modify markers.work ===
        markers_path = project_dir / "markers.work"
        print(f"Configuring markers.work")

        markers = MarkersFile.from_file(markers_path)

        for slot, frame_count in sample_counts.items():
            if frame_count > 0:
                markers.set_sample_length(slot=slot, length=frame_count)
                print(f"  - Slot {slot} sample length: {frame_count}")

        # Write markers file (auto-updates checksum)
        markers.to_file(markers_path)

        # === Create project.work ===
        print(f"Creating project.work")

        project = ProjectFile()

        # Add sample slots
        for track, slot, steps, sample_path in track_configs:
            project.add_sample_slot(
                slot_number=slot,
                path=sample_path,
                slot_type="FLEX",
                gain=48,
            )
            print(f"  - Slot {slot}: {os.path.basename(sample_path)}")

        # Add recorder slots (129-136)
        project.add_recorder_slots()

        project.to_file(project_dir / "project.work")

        # === Zip the project ===
        print(f"Zipping project to {zip_path}")
        zip_project(project_dir, zip_path)

    print(f"\nProject created: {zip_path}")
    print("\nTo copy to Octatrack, run:")
    print(f"  python tools/copy_project.py '{name}'")

    return zip_path


def main():
    parser = argparse.ArgumentParser(
        description="Create an Octatrack project with Flex machines using octapy library"
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
