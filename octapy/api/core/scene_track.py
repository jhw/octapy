"""
SceneTrack - standalone scene track locks for a single track.

This is a standalone object that owns its data and can be created
with constructor arguments or read from Part binary data.
"""

from __future__ import annotations

from typing import Optional

from ..._io import SceneParamsOffset, SCENE_PARAMS_SIZE, SCENE_LOCK_DISABLED
from ..enums import MachineType
from ._fx import FXAccessor
from ._src import SrcAccessor


class SceneTrack:
    """
    Scene parameter locks for a single track.

    This is a standalone object that owns its 32-byte data buffer.
    Each parameter can be None (no lock, use Part default) or a value (lock destination).

    Scene locks are used for crossfader morphing between Part defaults and scene values.

    Usage:
        # Create with constructor arguments
        track = SceneTrack(
            track_num=1,
            amp_volume=100,
            amp_attack=0,
        )

        # Read from Part binary (called by Scene)
        track = SceneTrack.read(track_num, track_data)

        # Write to binary
        data = track.write()
    """

    def __init__(
        self,
        track_num: int = 1,
        # Type hints for dynamic accessors (optional)
        machine_type: Optional[MachineType] = None,
        fx1_type: Optional[int] = None,
        fx2_type: Optional[int] = None,
        # Playback page locks
        playback_param1: Optional[int] = None,
        playback_param2: Optional[int] = None,
        playback_param3: Optional[int] = None,
        playback_param4: Optional[int] = None,
        playback_param5: Optional[int] = None,
        playback_param6: Optional[int] = None,
        # LFO page locks
        lfo_spd1: Optional[int] = None,
        lfo_spd2: Optional[int] = None,
        lfo_spd3: Optional[int] = None,
        lfo_dep1: Optional[int] = None,
        lfo_dep2: Optional[int] = None,
        lfo_dep3: Optional[int] = None,
        # AMP page locks
        amp_attack: Optional[int] = None,
        amp_hold: Optional[int] = None,
        amp_release: Optional[int] = None,
        amp_volume: Optional[int] = None,
        amp_balance: Optional[int] = None,
        # FX1 page locks
        fx1_param1: Optional[int] = None,
        fx1_param2: Optional[int] = None,
        fx1_param3: Optional[int] = None,
        fx1_param4: Optional[int] = None,
        fx1_param5: Optional[int] = None,
        fx1_param6: Optional[int] = None,
        # FX2 page locks
        fx2_param1: Optional[int] = None,
        fx2_param2: Optional[int] = None,
        fx2_param3: Optional[int] = None,
        fx2_param4: Optional[int] = None,
        fx2_param5: Optional[int] = None,
        fx2_param6: Optional[int] = None,
    ):
        """
        Create a SceneTrack with optional lock values.

        Args:
            track_num: Track number (1-8)
            machine_type: Optional machine type (for src accessor named params)
            fx1_type: Optional FX1 type (for fx1 accessor named params)
            fx2_type: Optional FX2 type (for fx2 accessor named params)
            All other args: Lock values (None = no lock, 0-127 = lock destination)
        """
        self._track_num = track_num
        self._machine_type = machine_type
        self._fx1_type = fx1_type
        self._fx2_type = fx2_type
        # Initialize all locks to disabled (255)
        self._data = bytearray([SCENE_LOCK_DISABLED] * SCENE_PARAMS_SIZE)

        # Apply any provided locks
        if playback_param1 is not None:
            self.playback_param1 = playback_param1
        if playback_param2 is not None:
            self.playback_param2 = playback_param2
        if playback_param3 is not None:
            self.playback_param3 = playback_param3
        if playback_param4 is not None:
            self.playback_param4 = playback_param4
        if playback_param5 is not None:
            self.playback_param5 = playback_param5
        if playback_param6 is not None:
            self.playback_param6 = playback_param6

        if lfo_spd1 is not None:
            self.lfo_spd1 = lfo_spd1
        if lfo_spd2 is not None:
            self.lfo_spd2 = lfo_spd2
        if lfo_spd3 is not None:
            self.lfo_spd3 = lfo_spd3
        if lfo_dep1 is not None:
            self.lfo_dep1 = lfo_dep1
        if lfo_dep2 is not None:
            self.lfo_dep2 = lfo_dep2
        if lfo_dep3 is not None:
            self.lfo_dep3 = lfo_dep3

        if amp_attack is not None:
            self.amp_attack = amp_attack
        if amp_hold is not None:
            self.amp_hold = amp_hold
        if amp_release is not None:
            self.amp_release = amp_release
        if amp_volume is not None:
            self.amp_volume = amp_volume
        if amp_balance is not None:
            self.amp_balance = amp_balance

        if fx1_param1 is not None:
            self.fx1_param1 = fx1_param1
        if fx1_param2 is not None:
            self.fx1_param2 = fx1_param2
        if fx1_param3 is not None:
            self.fx1_param3 = fx1_param3
        if fx1_param4 is not None:
            self.fx1_param4 = fx1_param4
        if fx1_param5 is not None:
            self.fx1_param5 = fx1_param5
        if fx1_param6 is not None:
            self.fx1_param6 = fx1_param6

        if fx2_param1 is not None:
            self.fx2_param1 = fx2_param1
        if fx2_param2 is not None:
            self.fx2_param2 = fx2_param2
        if fx2_param3 is not None:
            self.fx2_param3 = fx2_param3
        if fx2_param4 is not None:
            self.fx2_param4 = fx2_param4
        if fx2_param5 is not None:
            self.fx2_param5 = fx2_param5
        if fx2_param6 is not None:
            self.fx2_param6 = fx2_param6

    @classmethod
    def read(
        cls,
        track_num: int,
        track_data: bytes,
        machine_type: Optional[MachineType] = None,
        fx1_type: Optional[int] = None,
        fx2_type: Optional[int] = None,
    ) -> "SceneTrack":
        """
        Read a SceneTrack from binary data.

        Args:
            track_num: Track number (1-8)
            track_data: SCENE_PARAMS_SIZE bytes of track data
            machine_type: Optional machine type (for src accessor named params)
            fx1_type: Optional FX1 type (for fx1 accessor named params)
            fx2_type: Optional FX2 type (for fx2 accessor named params)

        Returns:
            SceneTrack instance
        """
        instance = cls.__new__(cls)
        instance._track_num = track_num
        instance._machine_type = machine_type
        instance._fx1_type = fx1_type
        instance._fx2_type = fx2_type
        instance._data = bytearray(track_data[:SCENE_PARAMS_SIZE])
        return instance

    def write(self) -> bytes:
        """
        Write this SceneTrack to binary data.

        Returns:
            SCENE_PARAMS_SIZE bytes
        """
        return bytes(self._data)

    def clone(self) -> "SceneTrack":
        """Create a copy of this SceneTrack."""
        instance = SceneTrack.__new__(SceneTrack)
        instance._track_num = self._track_num
        instance._machine_type = self._machine_type
        instance._fx1_type = self._fx1_type
        instance._fx2_type = self._fx2_type
        instance._data = bytearray(self._data)
        return instance

    # === Basic properties ===

    @property
    def track_num(self) -> int:
        """Get the track number (1-8)."""
        return self._track_num

    # === Lock get/set helpers ===

    def _get_lock(self, offset: int) -> Optional[int]:
        """Get a lock value. Returns None if disabled (255)."""
        value = self._data[offset]
        return None if value == SCENE_LOCK_DISABLED else value

    def _set_lock(self, offset: int, value: Optional[int]):
        """Set a lock value. None disables the lock."""
        if value is None:
            self._data[offset] = SCENE_LOCK_DISABLED
        else:
            self._data[offset] = value & 0x7F

    # === Playback page locks ===

    @property
    def playback_param1(self) -> Optional[int]:
        """Get/set playback param 1 lock (machine-specific)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM1)

    @playback_param1.setter
    def playback_param1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM1, value)

    @property
    def playback_param2(self) -> Optional[int]:
        """Get/set playback param 2 lock (machine-specific)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM2)

    @playback_param2.setter
    def playback_param2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM2, value)

    @property
    def playback_param3(self) -> Optional[int]:
        """Get/set playback param 3 lock (machine-specific)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM3)

    @playback_param3.setter
    def playback_param3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM3, value)

    @property
    def playback_param4(self) -> Optional[int]:
        """Get/set playback param 4 lock (machine-specific)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM4)

    @playback_param4.setter
    def playback_param4(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM4, value)

    @property
    def playback_param5(self) -> Optional[int]:
        """Get/set playback param 5 lock (machine-specific)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM5)

    @playback_param5.setter
    def playback_param5(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM5, value)

    @property
    def playback_param6(self) -> Optional[int]:
        """Get/set playback param 6 lock (machine-specific)."""
        return self._get_lock(SceneParamsOffset.PLAYBACK_PARAM6)

    @playback_param6.setter
    def playback_param6(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.PLAYBACK_PARAM6, value)

    # === Dynamic accessors (named parameter access) ===

    def _get_playback_param(self, n: int) -> Optional[int]:
        """Get playback param n (1-6)."""
        return getattr(self, f'playback_param{n}')

    def _set_playback_param(self, n: int, value: Optional[int]):
        """Set playback param n (1-6)."""
        setattr(self, f'playback_param{n}', value)

    @property
    def src(self) -> SrcAccessor:
        """
        Get SRC page accessor for named parameter access.

        Requires machine_type to be set for named access.

        Usage:
            track = SceneTrack(track_num=1, machine_type=MachineType.FLEX)
            track.src.pitch = 64       # Lock pitch to 64
            track.src.retrig_time = 79 # Lock retrig_time to 79

            track = SceneTrack(track_num=1, machine_type=MachineType.THRU)
            track.src.in_ab = 1        # Lock in_ab to 1
            track.src.vol_ab = 100     # Lock vol_ab to 100

        Returns:
            SrcAccessor with dynamic attribute access
        """
        if not hasattr(self, '_src_accessor'):
            self._src_accessor = SrcAccessor(
                track=self,
                get_machine_type=lambda: self._machine_type,
                get_param=self._get_playback_param,
                set_param=self._set_playback_param,
            )
        return self._src_accessor

    def _get_fx1_param(self, n: int) -> Optional[int]:
        """Get FX1 param n (1-6)."""
        return getattr(self, f'fx1_param{n}')

    def _set_fx1_param(self, n: int, value: Optional[int]):
        """Set FX1 param n (1-6)."""
        setattr(self, f'fx1_param{n}', value)

    @property
    def fx1(self) -> FXAccessor:
        """
        Get FX1 accessor for named parameter access.

        Requires fx1_type to be set for named access.

        Usage:
            track = SceneTrack(track_num=1, fx1_type=FX1Type.FILTER)
            track.fx1.base = 64      # Lock filter base to 64
            track.fx1.decay = 100    # Lock filter decay to 100

        Returns:
            FXAccessor with dynamic attribute access
        """
        if not hasattr(self, '_fx1_accessor'):
            self._fx1_accessor = FXAccessor(
                track=self,
                slot=1,
                get_type=lambda: self._fx1_type,
                set_type=None,  # SceneTrack doesn't store FX type
                get_param=self._get_fx1_param,
                set_param=self._set_fx1_param,
            )
        return self._fx1_accessor

    def _get_fx2_param(self, n: int) -> Optional[int]:
        """Get FX2 param n (1-6)."""
        return getattr(self, f'fx2_param{n}')

    def _set_fx2_param(self, n: int, value: Optional[int]):
        """Set FX2 param n (1-6)."""
        setattr(self, f'fx2_param{n}', value)

    @property
    def fx2(self) -> FXAccessor:
        """
        Get FX2 accessor for named parameter access.

        Requires fx2_type to be set for named access.

        Usage:
            track = SceneTrack(track_num=1, fx2_type=FX2Type.DELAY)
            track.fx2.time = 64      # Lock delay time to 64
            track.fx2.send = 100     # Lock delay send to 100

        Returns:
            FXAccessor with dynamic attribute access
        """
        if not hasattr(self, '_fx2_accessor'):
            self._fx2_accessor = FXAccessor(
                track=self,
                slot=2,
                get_type=lambda: self._fx2_type,
                set_type=None,  # SceneTrack doesn't store FX type
                get_param=self._get_fx2_param,
                set_param=self._set_fx2_param,
            )
        return self._fx2_accessor

    # === LFO page locks ===

    @property
    def lfo_spd1(self) -> Optional[int]:
        """Get/set LFO 1 speed lock."""
        return self._get_lock(SceneParamsOffset.LFO_SPD1)

    @lfo_spd1.setter
    def lfo_spd1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.LFO_SPD1, value)

    @property
    def lfo_spd2(self) -> Optional[int]:
        """Get/set LFO 2 speed lock."""
        return self._get_lock(SceneParamsOffset.LFO_SPD2)

    @lfo_spd2.setter
    def lfo_spd2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.LFO_SPD2, value)

    @property
    def lfo_spd3(self) -> Optional[int]:
        """Get/set LFO 3 speed lock."""
        return self._get_lock(SceneParamsOffset.LFO_SPD3)

    @lfo_spd3.setter
    def lfo_spd3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.LFO_SPD3, value)

    @property
    def lfo_dep1(self) -> Optional[int]:
        """Get/set LFO 1 depth lock."""
        return self._get_lock(SceneParamsOffset.LFO_DEP1)

    @lfo_dep1.setter
    def lfo_dep1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.LFO_DEP1, value)

    @property
    def lfo_dep2(self) -> Optional[int]:
        """Get/set LFO 2 depth lock."""
        return self._get_lock(SceneParamsOffset.LFO_DEP2)

    @lfo_dep2.setter
    def lfo_dep2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.LFO_DEP2, value)

    @property
    def lfo_dep3(self) -> Optional[int]:
        """Get/set LFO 3 depth lock."""
        return self._get_lock(SceneParamsOffset.LFO_DEP3)

    @lfo_dep3.setter
    def lfo_dep3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.LFO_DEP3, value)

    # === AMP page locks ===

    @property
    def amp_attack(self) -> Optional[int]:
        """Get/set AMP attack lock."""
        return self._get_lock(SceneParamsOffset.AMP_ATK)

    @amp_attack.setter
    def amp_attack(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_ATK, value)

    @property
    def amp_hold(self) -> Optional[int]:
        """Get/set AMP hold lock."""
        return self._get_lock(SceneParamsOffset.AMP_HOLD)

    @amp_hold.setter
    def amp_hold(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_HOLD, value)

    @property
    def amp_release(self) -> Optional[int]:
        """Get/set AMP release lock."""
        return self._get_lock(SceneParamsOffset.AMP_REL)

    @amp_release.setter
    def amp_release(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_REL, value)

    @property
    def amp_volume(self) -> Optional[int]:
        """Get/set AMP volume lock."""
        return self._get_lock(SceneParamsOffset.AMP_VOL)

    @amp_volume.setter
    def amp_volume(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_VOL, value)

    @property
    def amp_balance(self) -> Optional[int]:
        """Get/set AMP balance lock."""
        return self._get_lock(SceneParamsOffset.AMP_BAL)

    @amp_balance.setter
    def amp_balance(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.AMP_BAL, value)

    # === FX1 page locks ===

    @property
    def fx1_param1(self) -> Optional[int]:
        """Get/set FX1 param 1 lock."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM1)

    @fx1_param1.setter
    def fx1_param1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM1, value)

    @property
    def fx1_param2(self) -> Optional[int]:
        """Get/set FX1 param 2 lock."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM2)

    @fx1_param2.setter
    def fx1_param2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM2, value)

    @property
    def fx1_param3(self) -> Optional[int]:
        """Get/set FX1 param 3 lock."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM3)

    @fx1_param3.setter
    def fx1_param3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM3, value)

    @property
    def fx1_param4(self) -> Optional[int]:
        """Get/set FX1 param 4 lock."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM4)

    @fx1_param4.setter
    def fx1_param4(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM4, value)

    @property
    def fx1_param5(self) -> Optional[int]:
        """Get/set FX1 param 5 lock."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM5)

    @fx1_param5.setter
    def fx1_param5(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM5, value)

    @property
    def fx1_param6(self) -> Optional[int]:
        """Get/set FX1 param 6 lock."""
        return self._get_lock(SceneParamsOffset.FX1_PARAM6)

    @fx1_param6.setter
    def fx1_param6(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX1_PARAM6, value)

    # === FX2 page locks ===

    @property
    def fx2_param1(self) -> Optional[int]:
        """Get/set FX2 param 1 lock."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM1)

    @fx2_param1.setter
    def fx2_param1(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM1, value)

    @property
    def fx2_param2(self) -> Optional[int]:
        """Get/set FX2 param 2 lock."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM2)

    @fx2_param2.setter
    def fx2_param2(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM2, value)

    @property
    def fx2_param3(self) -> Optional[int]:
        """Get/set FX2 param 3 lock."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM3)

    @fx2_param3.setter
    def fx2_param3(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM3, value)

    @property
    def fx2_param4(self) -> Optional[int]:
        """Get/set FX2 param 4 lock."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM4)

    @fx2_param4.setter
    def fx2_param4(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM4, value)

    @property
    def fx2_param5(self) -> Optional[int]:
        """Get/set FX2 param 5 lock."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM5)

    @fx2_param5.setter
    def fx2_param5(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM5, value)

    @property
    def fx2_param6(self) -> Optional[int]:
        """Get/set FX2 param 6 lock."""
        return self._get_lock(SceneParamsOffset.FX2_PARAM6)

    @fx2_param6.setter
    def fx2_param6(self, value: Optional[int]):
        self._set_lock(SceneParamsOffset.FX2_PARAM6, value)

    # === Utility methods ===

    def clear_all_locks(self):
        """Clear all locks (set all to 255)."""
        for i in range(SCENE_PARAMS_SIZE):
            self._data[i] = SCENE_LOCK_DISABLED

    @property
    def is_blank(self) -> bool:
        """Check if this track has no locks set."""
        return all(b == SCENE_LOCK_DISABLED for b in self._data)

    def has_locks(self) -> bool:
        """Check if this track has any locks set."""
        return not self.is_blank

    # === Serialization ===

    def to_dict(self) -> dict:
        """
        Convert scene track locks to dictionary.

        Only includes locks that are set (not None).
        """
        result = {"track": self._track_num}

        # Playback locks
        playback = {}
        if self.playback_param1 is not None:
            playback["param1"] = self.playback_param1
        if self.playback_param2 is not None:
            playback["param2"] = self.playback_param2
        if self.playback_param3 is not None:
            playback["param3"] = self.playback_param3
        if self.playback_param4 is not None:
            playback["param4"] = self.playback_param4
        if self.playback_param5 is not None:
            playback["param5"] = self.playback_param5
        if self.playback_param6 is not None:
            playback["param6"] = self.playback_param6
        if playback:
            result["playback"] = playback

        # LFO locks
        lfo = {}
        if self.lfo_spd1 is not None:
            lfo["spd1"] = self.lfo_spd1
        if self.lfo_spd2 is not None:
            lfo["spd2"] = self.lfo_spd2
        if self.lfo_spd3 is not None:
            lfo["spd3"] = self.lfo_spd3
        if self.lfo_dep1 is not None:
            lfo["dep1"] = self.lfo_dep1
        if self.lfo_dep2 is not None:
            lfo["dep2"] = self.lfo_dep2
        if self.lfo_dep3 is not None:
            lfo["dep3"] = self.lfo_dep3
        if lfo:
            result["lfo"] = lfo

        # AMP locks
        amp = {}
        if self.amp_attack is not None:
            amp["attack"] = self.amp_attack
        if self.amp_hold is not None:
            amp["hold"] = self.amp_hold
        if self.amp_release is not None:
            amp["release"] = self.amp_release
        if self.amp_volume is not None:
            amp["volume"] = self.amp_volume
        if self.amp_balance is not None:
            amp["balance"] = self.amp_balance
        if amp:
            result["amp"] = amp

        # FX1 locks
        fx1 = {}
        if self.fx1_param1 is not None:
            fx1["param1"] = self.fx1_param1
        if self.fx1_param2 is not None:
            fx1["param2"] = self.fx1_param2
        if self.fx1_param3 is not None:
            fx1["param3"] = self.fx1_param3
        if self.fx1_param4 is not None:
            fx1["param4"] = self.fx1_param4
        if self.fx1_param5 is not None:
            fx1["param5"] = self.fx1_param5
        if self.fx1_param6 is not None:
            fx1["param6"] = self.fx1_param6
        if fx1:
            result["fx1"] = fx1

        # FX2 locks
        fx2 = {}
        if self.fx2_param1 is not None:
            fx2["param1"] = self.fx2_param1
        if self.fx2_param2 is not None:
            fx2["param2"] = self.fx2_param2
        if self.fx2_param3 is not None:
            fx2["param3"] = self.fx2_param3
        if self.fx2_param4 is not None:
            fx2["param4"] = self.fx2_param4
        if self.fx2_param5 is not None:
            fx2["param5"] = self.fx2_param5
        if self.fx2_param6 is not None:
            fx2["param6"] = self.fx2_param6
        if fx2:
            result["fx2"] = fx2

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "SceneTrack":
        """Create a SceneTrack from a dictionary."""
        kwargs = {"track_num": data.get("track", 1)}

        if "playback" in data:
            playback = data["playback"]
            if "param1" in playback:
                kwargs["playback_param1"] = playback["param1"]
            if "param2" in playback:
                kwargs["playback_param2"] = playback["param2"]
            if "param3" in playback:
                kwargs["playback_param3"] = playback["param3"]
            if "param4" in playback:
                kwargs["playback_param4"] = playback["param4"]
            if "param5" in playback:
                kwargs["playback_param5"] = playback["param5"]
            if "param6" in playback:
                kwargs["playback_param6"] = playback["param6"]

        if "lfo" in data:
            lfo = data["lfo"]
            if "spd1" in lfo:
                kwargs["lfo_spd1"] = lfo["spd1"]
            if "spd2" in lfo:
                kwargs["lfo_spd2"] = lfo["spd2"]
            if "spd3" in lfo:
                kwargs["lfo_spd3"] = lfo["spd3"]
            if "dep1" in lfo:
                kwargs["lfo_dep1"] = lfo["dep1"]
            if "dep2" in lfo:
                kwargs["lfo_dep2"] = lfo["dep2"]
            if "dep3" in lfo:
                kwargs["lfo_dep3"] = lfo["dep3"]

        if "amp" in data:
            amp = data["amp"]
            if "attack" in amp:
                kwargs["amp_attack"] = amp["attack"]
            if "hold" in amp:
                kwargs["amp_hold"] = amp["hold"]
            if "release" in amp:
                kwargs["amp_release"] = amp["release"]
            if "volume" in amp:
                kwargs["amp_volume"] = amp["volume"]
            if "balance" in amp:
                kwargs["amp_balance"] = amp["balance"]

        if "fx1" in data:
            fx1 = data["fx1"]
            for i in range(1, 7):
                key = f"param{i}"
                if key in fx1:
                    kwargs[f"fx1_param{i}"] = fx1[key]

        if "fx2" in data:
            fx2 = data["fx2"]
            for i in range(1, 7):
                key = f"param{i}"
                if key in fx2:
                    kwargs[f"fx2_param{i}"] = fx2[key]

        return cls(**kwargs)

    def __eq__(self, other) -> bool:
        """Check equality based on data buffer."""
        if not isinstance(other, SceneTrack):
            return NotImplemented
        return self._track_num == other._track_num and self._data == other._data

    def __repr__(self) -> str:
        locks = sum(1 for b in self._data if b != SCENE_LOCK_DISABLED)
        return f"SceneTrack(track={self._track_num}, locks={locks})"
