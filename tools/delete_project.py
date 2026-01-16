#!/usr/bin/env python3
"""
Remove a project from the connected Octatrack device.
"""

import argparse
import os
import shutil
import sys

OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"


def remove_project(name):
    """Remove a project from the Octatrack."""
    if not os.path.exists(OCTATRACK_DEVICE):
        print(f"Error: Octatrack not found at {OCTATRACK_DEVICE}")
        print("Make sure the device is connected and mounted.")
        sys.exit(1)

    project_path = os.path.join(OCTATRACK_DEVICE, name)
    audio_path = os.path.join(OCTATRACK_DEVICE, "AUDIO", name)

    if not os.path.exists(project_path):
        print(f"Error: Project '{name}' not found on device")
        print(f"Path: {project_path}")
        sys.exit(1)

    if not os.path.isdir(project_path):
        print(f"Error: '{name}' is not a directory")
        sys.exit(1)

    # Verify it's a project directory
    project_work = os.path.join(project_path, "project.work")
    if not os.path.exists(project_work):
        print(f"Error: '{name}' does not appear to be an Octatrack project")
        print("(missing project.work file)")
        sys.exit(1)

    print(f"Removing project '{name}' from {OCTATRACK_DEVICE}")
    shutil.rmtree(project_path)

    # Also remove the project's audio folder if it exists
    if os.path.exists(audio_path):
        print(f"Removing audio folder: {audio_path}")
        shutil.rmtree(audio_path)

    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Remove a project from the Octatrack"
    )
    parser.add_argument(
        "name",
        help="Project name to remove (required)"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Normalize to uppercase
    name = args.name.upper()

    # Confirm deletion unless --force is used
    if not args.force:
        response = input(f"Remove project '{name}' from Octatrack? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    remove_project(name)


if __name__ == "__main__":
    main()
