#!/usr/bin/env python3
"""
Remove a project from the local staging directory (tmp/).
"""

import argparse
import shutil
import sys
from pathlib import Path

TMP_DIR = Path(__file__).parent.parent / "tmp"


def remove_project(name, local_dir):
    """Remove a project (zip or directory) from the local directory."""
    local_path = Path(local_dir)
    zip_path = local_path / f"{name}.zip"
    dir_path = local_path / name

    removed = []

    # Remove zip file if exists
    if zip_path.exists():
        print(f"Removing {zip_path}")
        zip_path.unlink()
        removed.append("zip")

    # Remove directory if exists
    if dir_path.exists() and dir_path.is_dir():
        print(f"Removing {dir_path}")
        shutil.rmtree(dir_path)
        removed.append("directory")

    if not removed:
        print(f"Error: Project '{name}' not found in {local_dir}")
        print(f"  Checked: {zip_path}")
        print(f"           {dir_path}")
        sys.exit(1)

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
        default=str(TMP_DIR),
        help=f"Local directory (default: {TMP_DIR})"
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
