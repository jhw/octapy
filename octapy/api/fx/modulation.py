"""
Modulation FX classes (Phaser, Flanger, Chorus, Comb Filter).
"""

from .base import BaseFX


class PhaserFX(BaseFX):
    """
    Phaser effect container.

    Encoders:
        A: center    - Center frequency
        B: depth     - Modulation depth
        C: spread    - Stereo spread
        D: feedback  - Feedback amount
        E: width     - Stereo width
        F: mix       - Wet/dry mix
    """

    @property
    def center(self) -> int:
        """Get/set center frequency (0-127)."""
        return self._get_param(0)

    @center.setter
    def center(self, value: int):
        self._set_param(0, value)

    @property
    def depth(self) -> int:
        """Get/set modulation depth (0-127)."""
        return self._get_param(1)

    @depth.setter
    def depth(self, value: int):
        self._set_param(1, value)

    @property
    def spread(self) -> int:
        """Get/set stereo spread (0-127)."""
        return self._get_param(2)

    @spread.setter
    def spread(self, value: int):
        self._set_param(2, value)

    @property
    def feedback(self) -> int:
        """Get/set feedback amount (0-127)."""
        return self._get_param(3)

    @feedback.setter
    def feedback(self, value: int):
        self._set_param(3, value)

    @property
    def width(self) -> int:
        """Get/set stereo width (0-127)."""
        return self._get_param(4)

    @width.setter
    def width(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)


class FlangerFX(BaseFX):
    """
    Flanger effect container.

    Encoders:
        A: delay     - Delay time
        B: depth     - Modulation depth
        C: spread    - Stereo spread
        D: feedback  - Feedback amount
        E: width     - Stereo width
        F: mix       - Wet/dry mix
    """

    @property
    def delay(self) -> int:
        """Get/set delay time (0-127)."""
        return self._get_param(0)

    @delay.setter
    def delay(self, value: int):
        self._set_param(0, value)

    @property
    def depth(self) -> int:
        """Get/set modulation depth (0-127)."""
        return self._get_param(1)

    @depth.setter
    def depth(self, value: int):
        self._set_param(1, value)

    @property
    def spread(self) -> int:
        """Get/set stereo spread (0-127)."""
        return self._get_param(2)

    @spread.setter
    def spread(self, value: int):
        self._set_param(2, value)

    @property
    def feedback(self) -> int:
        """Get/set feedback amount (0-127)."""
        return self._get_param(3)

    @feedback.setter
    def feedback(self, value: int):
        self._set_param(3, value)

    @property
    def width(self) -> int:
        """Get/set stereo width (0-127)."""
        return self._get_param(4)

    @width.setter
    def width(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)


class ChorusFX(BaseFX):
    """
    Chorus effect container.

    Encoders:
        A: delay     - Delay time
        B: depth     - Modulation depth
        C: spread    - Stereo spread
        D: feedback  - Feedback amount
        E: width     - Stereo width
        F: mix       - Wet/dry mix
    """

    @property
    def delay(self) -> int:
        """Get/set delay time (0-127)."""
        return self._get_param(0)

    @delay.setter
    def delay(self, value: int):
        self._set_param(0, value)

    @property
    def depth(self) -> int:
        """Get/set modulation depth (0-127)."""
        return self._get_param(1)

    @depth.setter
    def depth(self, value: int):
        self._set_param(1, value)

    @property
    def spread(self) -> int:
        """Get/set stereo spread (0-127)."""
        return self._get_param(2)

    @spread.setter
    def spread(self, value: int):
        self._set_param(2, value)

    @property
    def feedback(self) -> int:
        """Get/set feedback amount (0-127)."""
        return self._get_param(3)

    @feedback.setter
    def feedback(self, value: int):
        self._set_param(3, value)

    @property
    def width(self) -> int:
        """Get/set stereo width (0-127)."""
        return self._get_param(4)

    @width.setter
    def width(self, value: int):
        self._set_param(4, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)


class CombFilterFX(BaseFX):
    """
    Comb filter effect container.

    Encoders:
        A: pitch     - Pitch
        B: tune      - Fine tune
        C: low_pass  - Low-pass filter
        D: feedback  - Feedback amount
        E: (unused)
        F: mix       - Wet/dry mix
    """

    @property
    def pitch(self) -> int:
        """Get/set pitch (0-127)."""
        return self._get_param(0)

    @pitch.setter
    def pitch(self, value: int):
        self._set_param(0, value)

    @property
    def tune(self) -> int:
        """Get/set fine tune (0-127)."""
        return self._get_param(1)

    @tune.setter
    def tune(self, value: int):
        self._set_param(1, value)

    @property
    def low_pass(self) -> int:
        """Get/set low-pass filter (0-127)."""
        return self._get_param(2)

    @low_pass.setter
    def low_pass(self, value: int):
        self._set_param(2, value)

    @property
    def feedback(self) -> int:
        """Get/set feedback amount (0-127)."""
        return self._get_param(3)

    @feedback.setter
    def feedback(self, value: int):
        self._set_param(3, value)

    @property
    def mix(self) -> int:
        """Get/set wet/dry mix (0-127)."""
        return self._get_param(5)

    @mix.setter
    def mix(self, value: int):
        self._set_param(5, value)
