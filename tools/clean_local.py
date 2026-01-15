#!/usr/bin/env python3
"""
Clean all project zip files from the local tmp/ directory.
"""

import argparse
import sys
from pathlib import Path

TMP_DIR = Path(__file__).parent.parent / "tmp"


def clean_local(force: bool = False):
    """Remove all zip files from tmp/ directory."""
    if not TMP_DIR.exists():
        print(f"tmp/ directory does not exist: {TMP_DIR}")
        return

    zip_files = list(TMP_DIR.glob("*.zip"))

    if not zip_files:
        print("No zip files found in tmp/")
        return

    print(f"Found {len(zip_files)} zip file(s) in tmp/:")
    for f in zip_files:
        print(f"  {f.name}")

    if not force:
        response = input("\nRemove all? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    for f in zip_files:
        f.unlink()
        print(f"Removed {f.name}")

    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Clean all project zip files from tmp/"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()
    clean_local(args.force)


if __name__ == "__main__":
    main()
