#!/usr/bin/env python3
"""
Run the octapy test suite.

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py -v        # Run with verbose output
    python run_tests.py -k name   # Run tests matching 'name'
"""

import subprocess
import sys


def main():
    """Run pytest with any command line arguments."""
    args = ["python", "-m", "pytest", "tests/"]

    # Pass through any additional arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    else:
        # Default to showing test names
        args.append("-v")

    result = subprocess.run(args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
