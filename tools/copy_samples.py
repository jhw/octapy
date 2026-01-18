#!/usr/bin/env python3
"""
Copy sample pack(s) to the connected Octatrack device.

Searches tmp/samples for matching directories and asks to copy each one.
Sample packs are copied recursively to AUDIO/samples/{PACK}/ on the device.

Usage:
    copy_samples.py              # List all, ask to copy each
    copy_samples.py erica        # Find matching, ask to copy each
    copy_samples.py -f erica     # Copy all matching without prompting
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

OCTATRACK_DEVICE = "/Volumes/OCTATRACK/Woldo"
TMP_DIR = Path(__file__).parent.parent / "tmp" / "samples"


def find_matching_packs(pattern: str = None) -> list:
    """Find sample pack directories matching the pattern (case-insensitive)."""
    if not TMP_DIR.exists():
        return []

    packs = [d for d in TMP_DIR.iterdir() if d.is_dir()]

    if pattern:
        pattern_lower = pattern.lower()
        packs = [p for p in packs if pattern_lower in p.name.lower()]

    return sorted(packs, key=lambda p: p.name)


def copy_single_pack(pack_path: Path, force: bool = False) -> bool:
    """Copy a single sample pack to the Octatrack.

    Returns True if copied, False if skipped.
    """
    name = pack_path.name
    dest_path = Path(OCTATRACK_DEVICE) / "AUDIO" / "samples" / name

    # Check if destination already exists
    if dest_path.exists():
        if not force:
            response = input(f"    '{name}' exists on device. Overwrite? [y/N] ")
            if response.lower() != 'y':
                print(f"    Skipped.")
                return False
        shutil.rmtree(dest_path)

    # Copy pack recursively
    shutil.copytree(pack_path, dest_path)

    # Count files
    file_count = sum(1 for _ in dest_path.rglob("*") if _.is_file())
    print(f"    Copied '{name}' ({file_count} files)")

    return True


def copy_samples(pattern: str = None, force: bool = False):
    """Copy matching sample packs to the Octatrack."""
    if not os.path.exists(OCTATRACK_DEVICE):
        print(f"Error: Octatrack not found at {OCTATRACK_DEVICE}")
        print("Make sure the device is connected and mounted.")
        sys.exit(1)

    packs = find_matching_packs(pattern)

    if not packs:
        if pattern:
            print(f"No sample packs matching '{pattern}' found in {TMP_DIR}")
        else:
            print(f"No sample packs found in {TMP_DIR}")
        return

    if pattern:
        print(f"Found {len(packs)} sample pack(s) matching '{pattern}':")
    else:
        print(f"Found {len(packs)} sample pack(s) in {TMP_DIR}:")

    copied = 0
    for pack_path in packs:
        if force:
            print(f"  {pack_path.name}...")
            if copy_single_pack(pack_path, force=True):
                copied += 1
        else:
            response = input(f"  Copy {pack_path.name}? [y/N] ")
            if response.lower() == 'y':
                if copy_single_pack(pack_path, force=False):
                    copied += 1
            else:
                print(f"    Skipped.")

    print(f"\nCopied {copied} of {len(packs)} sample pack(s).")


def main():
    parser = argparse.ArgumentParser(
        description="Copy sample pack(s) to the Octatrack"
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
    copy_samples(args.pattern, args.force)


if __name__ == "__main__":
    main()
