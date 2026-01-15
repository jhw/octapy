#!/usr/bin/env python3
"""
Remove a project from the local staging directory.
"""

import argparse
import os
import shutil
import sys

DEFAULT_LOCAL_DIR = "/tmp"


def remove_project(name, local_dir):
    """Remove a project from the local directory."""
    project_path = os.path.join(local_dir, name)

    if not os.path.exists(project_path):
        print(f"Error: Project '{name}' not found")
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

    print(f"Removing project '{name}' from {local_dir}")
    shutil.rmtree(project_path)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Remove a project from the local staging directory"
    )
    parser.add_argument(
        "name",
        help="Project name to remove (required)"
    )
    parser.add_argument(
        "-d", "--directory",
        default=DEFAULT_LOCAL_DIR,
        help=f"Local directory (default: {DEFAULT_LOCAL_DIR})"
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
        response = input(f"Remove project '{name}' from {args.directory}? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    remove_project(name, args.directory)


if __name__ == "__main__":
    main()
