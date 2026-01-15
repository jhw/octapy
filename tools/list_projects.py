#!/usr/bin/env python3
"""
List all projects on the connected Octatrack device.
"""

import os
import sys

OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"


def is_project_dir(path):
    """Check if a directory is an Octatrack project (contains project.work)."""
    return os.path.isfile(os.path.join(path, "project.work"))


def list_projects():
    """List all projects on the Octatrack."""
    if not os.path.exists(OCTATRACK_DEVICE):
        print(f"Error: Octatrack not found at {OCTATRACK_DEVICE}")
        print("Make sure the device is connected and mounted.")
        sys.exit(1)

    print(f"Projects on {OCTATRACK_DEVICE}:\n")

    projects = []
    for entry in os.listdir(OCTATRACK_DEVICE):
        full_path = os.path.join(OCTATRACK_DEVICE, entry)
        if os.path.isdir(full_path) and is_project_dir(full_path):
            projects.append(entry)

    if not projects:
        print("  (no projects found)")
        return

    projects.sort()
    for project in projects:
        print(f"  {project}")

    print(f"\nTotal: {len(projects)} project(s)")


def main():
    list_projects()


if __name__ == "__main__":
    main()
