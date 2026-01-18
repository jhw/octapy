#!/usr/bin/env python3
"""
Copy project(s) to the connected Octatrack device.

Searches tmp/projects for matching zip files and asks to copy each one.
Bundled samples are automatically copied to AUDIO/projects/{PROJECT}/ on the device.

Usage:
    copy_project.py              # List all, ask to copy each
    copy_project.py flex         # Find matching, ask to copy each
    copy_project.py -f flex      # Copy all matching without prompting
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
TMP_DIR = Path(__file__).parent.parent / "tmp" / "projects"


def find_matching_zips(pattern: str = None) -> list:
    """Find zip files matching the pattern (case-insensitive)."""
    if not TMP_DIR.exists():
        return []

    zip_files = list(TMP_DIR.glob("*.zip"))

    if pattern:
        pattern_lower = pattern.lower()
        zip_files = [f for f in zip_files if pattern_lower in f.stem.lower()]

    return sorted(zip_files, key=lambda f: f.name)


def copy_single_project(zip_path: Path, force: bool = False) -> bool:
    """Copy a single project to the Octatrack.

    Returns True if copied, False if skipped.
    """
    project = Project.from_zip(zip_path)
    name = project.name
    dest_path = Path(OCTATRACK_DEVICE) / name
    audio_dest = Path(OCTATRACK_DEVICE) / "AUDIO" / "projects" / name

    # Check if destination already exists
    if dest_path.exists():
        if not force:
            response = input(f"    '{name}' exists on device. Overwrite? [y/N] ")
            if response.lower() != 'y':
                print(f"    Skipped.")
                return False
        shutil.rmtree(dest_path)

    # Check if audio folder exists
    if audio_dest.exists():
        shutil.rmtree(audio_dest)

    # Save project to destination (this writes .work files)
    project.to_directory(dest_path)

    # Copy bundled samples to AUDIO/projects/{PROJECT}/
    sample_pool = project.sample_pool
    if sample_pool:
        audio_dest.mkdir(parents=True, exist_ok=True)
        for filename, local_path in sample_pool.items():
            shutil.copy2(local_path, audio_dest / filename)
        print(f"    Copied '{name}' ({len(sample_pool)} samples)")
    else:
        print(f"    Copied '{name}'")

    return True


def copy_projects(pattern: str = None, force: bool = False):
    """Copy matching projects to the Octatrack."""
    if not os.path.exists(OCTATRACK_DEVICE):
        print(f"Error: Octatrack not found at {OCTATRACK_DEVICE}")
        print("Make sure the device is connected and mounted.")
        sys.exit(1)

    zip_files = find_matching_zips(pattern)

    if not zip_files:
        if pattern:
            print(f"No zip files matching '{pattern}' found in {TMP_DIR}")
        else:
            print(f"No zip files found in {TMP_DIR}")
        return

    if pattern:
        print(f"Found {len(zip_files)} project(s) matching '{pattern}':")
    else:
        print(f"Found {len(zip_files)} project(s) in {TMP_DIR}:")

    copied = 0
    for zip_path in zip_files:
        if force:
            print(f"  {zip_path.stem}...")
            if copy_single_project(zip_path, force=True):
                copied += 1
        else:
            response = input(f"  Copy {zip_path.stem}? [y/N] ")
            if response.lower() == 'y':
                if copy_single_project(zip_path, force=False):
                    copied += 1
            else:
                print(f"    Skipped.")

    print(f"\nCopied {copied} of {len(zip_files)} project(s).")
    if copied > 0:
        print("\nNote: You may need to reload the project(s) on the Octatrack.")


def main():
    parser = argparse.ArgumentParser(
        description="Copy project(s) to the Octatrack"
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        default=None,
        help="Text fragment to match (case-insensitive)"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Copy without prompting (overwrites existing)"
    )

    args = parser.parse_args()
    copy_projects(args.pattern, args.force)


if __name__ == "__main__":
    main()
