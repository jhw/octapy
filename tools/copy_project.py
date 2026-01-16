#!/usr/bin/env python3
"""
Copy a project to the connected Octatrack device.

Accepts either:
- A project name (looks in tmp/ directory, e.g., "HELLO FLEX")
- A zip file path (e.g., /path/to/HELLO FLEX.zip)
- A project directory path (e.g., /path/to/HELLO FLEX)

Before copying, verifies that all sample paths referenced in project.work
exist on the Octatrack device.
"""

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple

# Add parent to path so we can import octapy
sys.path.insert(0, str(Path(__file__).parent.parent))
from octapy._io import ProjectFile

OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"
TMP_DIR = Path(__file__).parent.parent / "tmp"


def check_sample_paths(project_work_path: Path) -> Tuple[List[str], List[str]]:
    """
    Check that all sample paths in project.work exist on the Octatrack.

    Args:
        project_work_path: Path to project.work file

    Returns:
        Tuple of (found_paths, missing_paths)
    """
    project = ProjectFile.from_file(project_work_path)

    found = []
    missing = []

    for slot in project.sample_slots:
        if not slot.path:
            continue  # Empty path (e.g., recorder slots)

        # Convert relative path to absolute path on device
        # Paths are like "../AUDIO/Erica Pico/sample.wav"
        if slot.path.startswith("../"):
            abs_path = Path(OCTATRACK_DEVICE) / slot.path[3:]
        else:
            abs_path = Path(OCTATRACK_DEVICE) / slot.path

        if abs_path.exists():
            found.append(slot.path)
        else:
            missing.append(slot.path)

    return found, missing


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

    if is_zip:
        # Extract project name from zip filename
        name = source_path.stem.upper()
        dest_path = Path(OCTATRACK_DEVICE) / name

        # Verify zip contains project.work and check sample paths
        with zipfile.ZipFile(source_path, 'r') as zf:
            if 'project.work' not in zf.namelist():
                print(f"Error: '{source_path}' does not appear to be an Octatrack project zip")
                print("(missing project.work file)")
                sys.exit(1)

            # Extract project.work to temp location to check sample paths
            with tempfile.TemporaryDirectory() as tmp:
                zf.extract('project.work', tmp)
                project_work_path = Path(tmp) / 'project.work'
                found, missing = check_sample_paths(project_work_path)
    else:
        # Source is a directory
        name = source_path.name.upper()
        dest_path = Path(OCTATRACK_DEVICE) / name

        # Verify it's a project directory
        project_work_path = source_path / "project.work"
        if not project_work_path.exists():
            print(f"Error: '{source_path}' does not appear to be an Octatrack project")
            print("(missing project.work file)")
            sys.exit(1)

        # Check sample paths
        found, missing = check_sample_paths(project_work_path)

    # Report sample path status
    if found:
        print(f"Found {len(found)} sample(s) on device")
    if missing:
        print(f"\nWarning: {len(missing)} sample(s) not found on device:")
        for path in missing:
            print(f"  - {path}")
        print()
        response = input("Continue anyway? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Check if destination already exists
    if dest_path.exists():
        print(f"Warning: Project '{name}' already exists on device")
        response = input("Overwrite? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        shutil.rmtree(dest_path)

    print(f"Copying '{name}' to {OCTATRACK_DEVICE}")

    if is_zip:
        # Unzip to destination
        dest_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source_path, 'r') as zf:
            zf.extractall(dest_path)
    else:
        # Copy directory
        shutil.copytree(source_path, dest_path)

    print("Done.")
    print("\nNote: You may need to reload the project on the Octatrack.")


def main():
    parser = argparse.ArgumentParser(
        description="Copy a project to the Octatrack"
    )
    parser.add_argument(
        "source",
        help="Project zip file or directory path"
    )

    args = parser.parse_args()

    copy_project(args.source)


if __name__ == "__main__":
    main()
