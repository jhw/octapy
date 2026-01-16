#!/usr/bin/env python3
"""
Copy a project to the connected Octatrack device.

Accepts either:
- A project name (looks in tmp/ directory, e.g., "HELLO FLEX")
- A zip file path (e.g., /path/to/HELLO FLEX.zip)
- A project directory path (e.g., /path/to/HELLO FLEX)

Bundled samples are automatically copied to AUDIO/{PROJECT}/ on the device.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Add parent to path so we can import octapy
sys.path.insert(0, str(Path(__file__).parent.parent))
from octapy import Project

OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"
TMP_DIR = Path(__file__).parent.parent / "tmp"


def copy_project(source: str):
    """Copy a project to the Octatrack."""
    if not os.path.exists(OCTATRACK_DEVICE):
        print(f"Error: Octatrack not found at {OCTATRACK_DEVICE}")
        print("Make sure the device is connected and mounted.")
        sys.exit(1)

    source_path = Path(source)

    # If source doesn't exist, check tmp/ directory for a zip with that name
    if not source_path.exists():
        # Try as project name in tmp/
        name = source.upper()
        tmp_zip = TMP_DIR / f"{name}.zip"
        if tmp_zip.exists():
            source_path = tmp_zip
        else:
            print(f"Error: Source not found at {source_path}")
            print(f"       Also checked: {tmp_zip}")
            sys.exit(1)

    # Determine if source is a zip file or directory
    is_zip = source_path.suffix.lower() == '.zip'

    # Load project using high-level API
    if is_zip:
        project = Project.from_zip(source_path)
    else:
        project = Project.from_directory(source_path)

    name = project.name
    dest_path = Path(OCTATRACK_DEVICE) / name
    audio_dest = Path(OCTATRACK_DEVICE) / "AUDIO" / name

    # Check if destination already exists
    if dest_path.exists():
        print(f"Warning: Project '{name}' already exists on device")
        response = input("Overwrite? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        shutil.rmtree(dest_path)

    # Check if audio folder exists
    if audio_dest.exists():
        print(f"Removing existing audio folder: {audio_dest}")
        shutil.rmtree(audio_dest)

    print(f"Copying '{name}' to {OCTATRACK_DEVICE}")

    # Save project to destination (this writes .work files)
    project.to_directory(dest_path)

    # Copy bundled samples to AUDIO/{PROJECT}/
    sample_pool = project.sample_pool
    if sample_pool:
        audio_dest.mkdir(parents=True, exist_ok=True)
        print(f"Copying {len(sample_pool)} sample(s) to {audio_dest}")
        for filename, local_path in sample_pool.items():
            shutil.copy2(local_path, audio_dest / filename)

    print("Done.")
    print("\nNote: You may need to reload the project on the Octatrack.")


def main():
    parser = argparse.ArgumentParser(
        description="Copy a project to the Octatrack"
    )
    parser.add_argument(
        "source",
        help="Project name, zip file, or directory path"
    )

    args = parser.parse_args()

    copy_project(args.source)


if __name__ == "__main__":
    main()
