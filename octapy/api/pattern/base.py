"""
BasePatternTrack - Abstract base class for pattern tracks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from ..step import BaseStep, _trig_mask_to_steps, _steps_to_trig_mask


class BasePatternTrack(ABC):
    """
    Abstract base class for pattern track sequence data.

    Provides shared functionality for step access and trig masks.
    Subclasses provide offset constants and step class.
    """

    def __init__(self, pattern: "Pattern", track_num: int):
        self._pattern = pattern
        self._track_num = track_num
        self._steps: Dict[int, BaseStep] = {}

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._pattern._bank._bank_file._data

    @abstractmethod
    def _track_offset(self) -> int:
        """Get the byte offset for this track in the bank file."""
        pass

    @property
    @abstractmethod
    def _trig_offset(self) -> int:
        """Offset to TRIG_TRIGGER within the track."""
        pass

    @property
    @abstractmethod
    def _trigless_offset(self) -> int:
        """Offset to TRIG_TRIGLESS within the track."""
        pass

    @abstractmethod
    def _create_step(self, step_num: int) -> BaseStep:
        """Create a step instance for this track type."""
        pass

    def step(self, step_num: int) -> BaseStep:
        """
        Get a specific step (1-64).

        Args:
            step_num: Step number (1-64)

        Returns:
            Step instance for this position
        """
        if step_num not in self._steps:
            self._steps[step_num] = self._create_step(step_num)
        return self._steps[step_num]

    @property
    def active_steps(self) -> List[int]:
        """Get/set active trigger steps (1-indexed list)."""
        offset = self._track_offset() + self._trig_offset
        return _trig_mask_to_steps(self._data, offset)

    @active_steps.setter
    def active_steps(self, value: List[int]):
        offset = self._track_offset() + self._trig_offset
        _steps_to_trig_mask(self._data, offset, value)

    @property
    def trigless_steps(self) -> List[int]:
        """Get/set trigless (envelope) steps (1-indexed list)."""
        offset = self._track_offset() + self._trigless_offset
        return _trig_mask_to_steps(self._data, offset)

    @trigless_steps.setter
    def trigless_steps(self, value: List[int]):
        offset = self._track_offset() + self._trigless_offset
        _steps_to_trig_mask(self._data, offset, value)
