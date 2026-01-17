"""
SlotManager - manages sample slot assignments for a project.
"""

from __future__ import annotations

from typing import Dict, Optional


# === Slot limits ===
MAX_FLEX_SAMPLE_SLOTS = 128  # Slots 1-128 for user samples
MAX_STATIC_SAMPLE_SLOTS = 128  # Slots 1-128 (separate pool from flex)
RECORDER_SLOTS_START = 129  # Recorder buffer slots 129-136


# === Slot exceptions ===

class OctapyError(Exception):
    """Base exception for octapy errors."""
    pass


class SlotLimitExceeded(OctapyError):
    """Raised when trying to add more samples than available slots."""
    pass


class InvalidSlotNumber(OctapyError):
    """Raised when a slot number is out of valid range."""
    pass


class SlotManager:
    """
    Manages sample slot assignments for flex and static samples.

    Tracks which slots are in use and handles auto-assignment of new slots.
    Flex and static samples have separate slot pools (1-128 each).
    """

    def __init__(self):
        # OT path -> slot number (1-128)
        self._flex_slots: Dict[str, int] = {}
        self._static_slots: Dict[str, int] = {}

    def _get_pool(self, slot_type: str) -> Dict[str, int]:
        """Get the slot pool for a slot type."""
        return self._flex_slots if slot_type.upper() == "FLEX" else self._static_slots

    def _max_slots(self, slot_type: str) -> int:
        """Get max slots for a slot type."""
        return MAX_FLEX_SAMPLE_SLOTS if slot_type.upper() == "FLEX" else MAX_STATIC_SAMPLE_SLOTS

    def get(self, ot_path: str, slot_type: str = "FLEX") -> Optional[int]:
        """
        Get the slot number for an OT path.

        Args:
            ot_path: OT-style path (e.g., "../AUDIO/PROJECT/sample.wav")
            slot_type: "FLEX" or "STATIC"

        Returns:
            Slot number (1-128) if found, None otherwise
        """
        return self._get_pool(slot_type).get(ot_path)

    def next_available(self, slot_type: str = "FLEX") -> int:
        """
        Find the next available slot number.

        Args:
            slot_type: "FLEX" or "STATIC"

        Returns:
            Next available slot number (1-128)

        Raises:
            SlotLimitExceeded: If all 128 slots are in use
        """
        pool = self._get_pool(slot_type)
        max_slots = self._max_slots(slot_type)
        used = set(pool.values())

        for slot in range(1, max_slots + 1):
            if slot not in used:
                return slot

        raise SlotLimitExceeded(
            f"All {max_slots} {slot_type.lower()} sample slots are in use"
        )

    def assign(
        self,
        ot_path: str,
        slot_type: str = "FLEX",
        slot: Optional[int] = None,
    ) -> int:
        """
        Assign a slot to an OT path.

        If the path already has a slot assigned, returns the existing slot.
        If no slot is specified, auto-assigns the next available slot.

        Args:
            ot_path: OT-style path (e.g., "../AUDIO/PROJECT/sample.wav")
            slot_type: "FLEX" or "STATIC"
            slot: Explicit slot number (1-128), or None for auto-assign

        Returns:
            The assigned slot number

        Raises:
            SlotLimitExceeded: If auto-assigning and all slots are used
            InvalidSlotNumber: If explicit slot is invalid or already in use
        """
        pool = self._get_pool(slot_type)
        max_slots = self._max_slots(slot_type)

        # Check if path already has a slot
        if ot_path in pool:
            return pool[ot_path]

        # Validate or auto-assign slot
        if slot is None:
            slot = self.next_available(slot_type)
        else:
            if slot < 1 or slot > max_slots:
                raise InvalidSlotNumber(
                    f"Slot {slot} is out of range. Valid range is 1-{max_slots}."
                )
            # Check if slot is already in use
            used = set(pool.values())
            if slot in used:
                for existing_path, existing_slot in pool.items():
                    if existing_slot == slot:
                        raise InvalidSlotNumber(
                            f"Slot {slot} is already in use by '{existing_path}'"
                        )

        # Assign the slot
        pool[ot_path] = slot
        return slot

    def load_from_slots(self, sample_slots) -> None:
        """
        Initialize slot tracking from existing sample slots.

        Args:
            sample_slots: List of SampleSlot objects from project file
        """
        for sample_slot in sample_slots:
            slot_num = sample_slot.slot_number
            path = sample_slot.path
            slot_type = sample_slot.slot_type.upper()

            # Skip recorder slots (129-136) and empty paths
            if slot_num >= RECORDER_SLOTS_START or not path:
                continue

            if slot_type == "FLEX":
                self._flex_slots[path] = slot_num
            elif slot_type == "STATIC":
                self._static_slots[path] = slot_num

    @property
    def flex_count(self) -> int:
        """Number of flex slots in use."""
        return len(self._flex_slots)

    @property
    def static_count(self) -> int:
        """Number of static slots in use."""
        return len(self._static_slots)

    @property
    def flex_paths(self) -> list:
        """List of all flex sample OT paths."""
        return list(self._flex_slots.keys())

    @property
    def static_paths(self) -> list:
        """List of all static sample OT paths."""
        return list(self._static_slots.keys())
