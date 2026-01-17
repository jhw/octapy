"""
BasePartTrack - abstract base class for part track configuration.
"""

from __future__ import annotations

from abc import ABC


class BasePartTrack(ABC):
    """
    Abstract base class for part track configuration.

    Provides shared functionality for accessing part data.
    Subclasses provide track-specific properties.
    """

    def __init__(self, part: "Part", track_num: int):
        self._part = part
        self._track_num = track_num

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._part._bank._bank_file._data

    def _part_offset(self) -> int:
        """Get the byte offset for this track's part in the bank file."""
        return self._part._bank._bank_file.part_offset(self._part._part_num)
