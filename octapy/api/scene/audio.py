"""
AudioSceneTrack - base scene track with AMP and FX locks.
"""

from __future__ import annotations

from typing import Optional

from ..._io import SceneParamsOffset
from .base import BaseSceneTrack


class AudioSceneTrack(BaseSceneTrack):
    """
    Audio scene track with AMP, FX1, and FX2 locks.

    This is the base class for all audio scene tracks.
    Machine-specific subclasses add playback page properties.

    Scene locks use None to indicate "no lock" (use Part default).
    Any other value is the scene's lock destination for crossfader morphing.

    Usage:
        scene = part.scene(1)
        track = scene.track(1)

        # Set AMP locks
        track.amp_volume = 100  # Lock volume to 100
        track.amp_attack = None  # Clear attack lock (use Part default)

        # FX locks work similarly
        track.fx1_param1 = 64
    """

    # === AMP Page Locks ===

    @property
    def amp_attack(self) -> Optional[int]:
        """Get/set AMP attack lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.AMP_ATK)

    @amp_attack.setter
    def amp_attack(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_ATK, value)

    @property
    def amp_hold(self) -> Optional[int]:
        """Get/set AMP hold lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.AMP_HOLD)

    @amp_hold.setter
    def amp_hold(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_HOLD, value)

    @property
    def amp_release(self) -> Optional[int]:
        """Get/set AMP release lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.AMP_REL)

    @amp_release.setter
    def amp_release(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_REL, value)

    @property
    def amp_volume(self) -> Optional[int]:
        """Get/set AMP volume lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.AMP_VOL)

    @amp_volume.setter
    def amp_volume(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_VOL, value)

    @property
    def amp_balance(self) -> Optional[int]:
        """Get/set AMP balance lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.AMP_BAL)

    @amp_balance.setter
    def amp_balance(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_BAL, value)

    # === FX1 Page Locks ===

    @property
    def fx1_param1(self) -> Optional[int]:
        """Get/set FX1 param 1 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM1)

    @fx1_param1.setter
    def fx1_param1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM1, value)

    @property
    def fx1_param2(self) -> Optional[int]:
        """Get/set FX1 param 2 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM2)

    @fx1_param2.setter
    def fx1_param2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM2, value)

    @property
    def fx1_param3(self) -> Optional[int]:
        """Get/set FX1 param 3 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM3)

    @fx1_param3.setter
    def fx1_param3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM3, value)

    @property
    def fx1_param4(self) -> Optional[int]:
        """Get/set FX1 param 4 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM4)

    @fx1_param4.setter
    def fx1_param4(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM4, value)

    @property
    def fx1_param5(self) -> Optional[int]:
        """Get/set FX1 param 5 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM5)

    @fx1_param5.setter
    def fx1_param5(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM5, value)

    @property
    def fx1_param6(self) -> Optional[int]:
        """Get/set FX1 param 6 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM6)

    @fx1_param6.setter
    def fx1_param6(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM6, value)

    # === FX2 Page Locks ===

    @property
    def fx2_param1(self) -> Optional[int]:
        """Get/set FX2 param 1 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM1)

    @fx2_param1.setter
    def fx2_param1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM1, value)

    @property
    def fx2_param2(self) -> Optional[int]:
        """Get/set FX2 param 2 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM2)

    @fx2_param2.setter
    def fx2_param2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM2, value)

    @property
    def fx2_param3(self) -> Optional[int]:
        """Get/set FX2 param 3 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM3)

    @fx2_param3.setter
    def fx2_param3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM3, value)

    @property
    def fx2_param4(self) -> Optional[int]:
        """Get/set FX2 param 4 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM4)

    @fx2_param4.setter
    def fx2_param4(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM4, value)

    @property
    def fx2_param5(self) -> Optional[int]:
        """Get/set FX2 param 5 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM5)

    @fx2_param5.setter
    def fx2_param5(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM5, value)

    @property
    def fx2_param6(self) -> Optional[int]:
        """Get/set FX2 param 6 lock (None = no lock)."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM6)

    @fx2_param6.setter
    def fx2_param6(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM6, value)
