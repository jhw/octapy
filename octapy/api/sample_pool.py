"""
SamplePool - scan and filter samples from a directory.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import List, Optional


class SamplePool:
    """
    A pool of samples scanned from a directory, optionally filtered by regex.

    Usage:
        from octapy import SamplePool

        kicks = SamplePool("samples/drums", r"BD")
        snares = SamplePool("samples/drums", r"SN|CP")
        hats = SamplePool("samples/drums", r"HH|OH|CH|CY|RM|PL")

        slot = project.add_sample(kicks.random())
    """

    def __init__(self, path: Path, pattern: Optional[str] = None):
        """
        Create a sample pool from a directory.

        Args:
            path: Directory to scan for .wav files (recursive)
            pattern: Optional regex pattern to filter filenames (case insensitive)
        """
        self.path = Path(path)
        self.pattern = re.compile(pattern, re.IGNORECASE) if pattern else None
        self._samples = self._scan()

    def _scan(self) -> List[Path]:
        """Scan directory for matching samples."""
        samples = []
        if not self.path.exists():
            return samples

        for wav in self.path.rglob("*.wav"):
            if self.pattern is None or self.pattern.search(wav.name):
                samples.append(wav)

        return sorted(samples)

    def random(self) -> Path:
        """Get a random sample from the pool."""
        if not self._samples:
            pattern_desc = f" matching '{self.pattern.pattern}'" if self.pattern else ""
            raise ValueError(f"No samples found{pattern_desc} in {self.path}")
        return random.choice(self._samples)

    def __len__(self) -> int:
        return len(self._samples)

    def __iter__(self):
        return iter(self._samples)

    def __bool__(self) -> bool:
        return len(self._samples) > 0

    def __repr__(self) -> str:
        pattern_str = f", pattern='{self.pattern.pattern}'" if self.pattern else ""
        return f"SamplePool({self.path}{pattern_str}, {len(self)} samples)"
