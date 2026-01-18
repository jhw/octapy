#!/usr/bin/env python3
"""
Remove project(s) from the connected Octatrack device.

Searches for matching projects on the device and asks to delete each one.

Usage:
    delete_project.py              # List all, ask to remove each
    delete_project.py flex         # Find matching, ask to remove each
    delete_project.py -f flex      # Remove all matching without prompting
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"


def is_project_dir(path: Path) -> bool:
    """Check if a directory is an Octatrack project (contains project.work)."""
    return (path / "project.work").exists()


def find_matching_projects(pattern: str = None) -> list:
    """Find projects matching the pattern (case-insensitive)."""
    device_path = Path(OCTATRACK_DEVICE)
    if not device_path.exists():
        return []

    projects = []
    for entry in device_path.iterdir():
        if entry.is_dir() and is_project_dir(entry):
            projects.append(entry)

    if pattern:
        pattern_lower = pattern.lower()
        projects = [p for p in projects if pattern_lower in p.name.lower()]

    return sorted(projects, key=lambda p: p.name)


def delete_single_project(project_path: Path) -> bool:
    """Delete a single project from the Octatrack.

    Returns True if deleted, False if skipped.
    """
    name = project_path.name
    audio_path = Path(OCTATRACK_DEVICE) / "AUDIO" / name

    shutil.rmtree(project_path)

    # Also remove the project's audio folder if it exists
    if audio_path.exists():
        shutil.rmtree(audio_path)
        print(f"    Removed '{name}' (+ audio folder)")
    else:
        print(f"    Removed '{name}'")

    return True


def delete_projects(pattern: str = None, force: bool = False):
    """Remove matching projects from the Octatrack."""
    if not os.path.exists(OCTATRACK_DEVICE):
        print(f"Error: Octatrack not found at {OCTATRACK_DEVICE}")
        print("Make sure the device is connected and mounted.")
        sys.exit(1)

    projects = find_matching_projects(pattern)

    if not projects:
        if pattern:
            print(f"No projects matching '{pattern}' found on device")
        else:
            print(f"No projects found on device")
        return

    if pattern:
        print(f"Found {len(projects)} project(s) matching '{pattern}':")
    else:
        print(f"Found {len(projects)} project(s) on device:")

    removed = 0
    for project_path in projects:
        if force:
            print(f"  {project_path.name}...")
            if delete_single_project(project_path):
                removed += 1
        else:
            response = input(f"  Remove {project_path.name}? [y/N] ")
            if response.lower() == 'y':
                if delete_single_project(project_path):
                    removed += 1
            else:
                print(f"    Skipped.")

    print(f"\nRemoved {removed} of {len(projects)} project(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Remove project(s) from the Octatrack"
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
        help="Remove without prompting"
    )

    args = parser.parse_args()
    delete_projects(args.pattern, args.force)


if __name__ == "__main__":
    main()
