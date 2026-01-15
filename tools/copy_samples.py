#!/usr/bin/env python3
"""
Copy samples to the Octatrack AUDIO folder.
"""

import argparse
import os
import shutil
import sys

OCTATRACK_AUDIO = "/Volumes/OCTATRACK/Woldo/AUDIO"
DEFAULT_SOURCE = "tmp/Erica Pico"


def copy_samples(source, dest_name=None, force=False):
    """Copy samples from source to Octatrack AUDIO folder."""
    if not os.path.exists(source):
        print(f"Error: Source directory '{source}' not found.")
        sys.exit(1)

    if not os.path.exists(OCTATRACK_AUDIO):
        print(f"Error: Octatrack not connected ('{OCTATRACK_AUDIO}' not found).")
        sys.exit(1)

    # Use source folder name if dest_name not specified
    if dest_name is None:
        dest_name = os.path.basename(source.rstrip('/'))

    dest_path = os.path.join(OCTATRACK_AUDIO, dest_name)

    if os.path.exists(dest_path):
        if not force:
            response = input(f"'{dest_path}' exists. Overwrite? [y/N] ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(0)
        print(f"Removing existing '{dest_path}'...")
        shutil.rmtree(dest_path)

    print(f"Copying '{source}' to '{dest_path}'...")
    shutil.copytree(source, dest_path)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Copy samples to the Octatrack AUDIO folder"
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=DEFAULT_SOURCE,
        help=f"Source directory (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument(
        "-n", "--name",
        help="Destination folder name (default: source folder name)"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite without confirmation"
    )

    args = parser.parse_args()
    copy_samples(args.source, args.name, args.force)


if __name__ == "__main__":
    main()
