#!/usr/bin/env python3
"""
Clean project zip files from the local tmp/projects directory.

Usage:
    clean_local.py              # List all, ask to remove each
    clean_local.py flex         # Find matching, ask to remove each
    clean_local.py -f           # Remove all without prompting
    clean_local.py -f flex      # Remove matching without prompting
"""

import argparse
import sys
from pathlib import Path

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


def clean_local(pattern: str = None, force: bool = False):
    """Remove zip files from tmp/projects directory."""
    if not TMP_DIR.exists():
        print(f"Directory does not exist: {TMP_DIR}")
        return

    zip_files = find_matching_zips(pattern)

    if not zip_files:
        if pattern:
            print(f"No zip files matching '{pattern}' found in {TMP_DIR}")
        else:
            print(f"No zip files found in {TMP_DIR}")
        return

    if pattern:
        print(f"Found {len(zip_files)} zip file(s) matching '{pattern}':")
    else:
        print(f"Found {len(zip_files)} zip file(s) in {TMP_DIR}:")

    if force:
        # Remove all matching without prompting
        for f in zip_files:
            f.unlink()
            print(f"  Removed {f.name}")
        print("Done.")
    else:
        # Ask for each file
        removed = 0
        for f in zip_files:
            response = input(f"  Remove {f.name}? [y/N] ")
            if response.lower() == 'y':
                f.unlink()
                print(f"    Removed.")
                removed += 1
            else:
                print(f"    Skipped.")

        print(f"\nRemoved {removed} of {len(zip_files)} file(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Clean project zip files from tmp/projects"
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
    clean_local(args.pattern, args.force)


if __name__ == "__main__":
    main()
