"""
RecorderSetup - standalone recorder buffer configuration.

This is a standalone object that owns its data buffer and can be created
with constructor arguments, read from binary, or written to binary.
"""

from __future__ import annotations

from typing import Optional

from ..._io import (
    RecorderSetupOffset,
    RECORDER_SETUP_SIZE,
    OCTAPY_DEFAULT_RECORDER_SETUP,
)
from ..enums import RecordingSource, RecTrigMode, QRecMode


class RecorderSetup:
    """
    Recorder buffer configuration for an audio track.

    This is a standalone object that can be created with constructor arguments
    or read from binary data. It owns its data buffer.

    Each audio track has its own recorder buffer. Track N always records
    to buffer N (fixed binding), but playback is flexible - any Flex
    machine can play any buffer via slots 129-136.

    Usage:
        # Create with constructor arguments
        recorder = RecorderSetup(
            source=RecordingSource.TRACK_3,
            rlen=16,
            trig=RecTrigMode.ONE,
            qrec=QRecMode.PLEN,
        )

        # Read from binary
        recorder = RecorderSetup.read(data)

        # Write to binary
        data = recorder.write()

    Setup Page 1 (FUNC+REC1):
        A: INAB   - External input AB selection (use source property instead)
        B: INCD   - External input CD selection (use source property instead)
        C: RLEN   - Recording length in steps (rlen property)
        D: TRIG   - Recording mode (trig property)
        E: SRC3   - Internal source track (use source property instead)
        F: LOOP   - Loop recording (loop property)

    Setup Page 2 (FUNC+REC2):
        A: FIN    - Fade in duration (fin property)
        B: FOUT   - Fade out duration (fout property)
        C: AB     - Input gain for AB (ab_gain property)
        D: QREC   - Quantize recording start (qrec property)
        E: QPL    - Quantize playback (qpl property)
        F: CD     - Input gain for CD (cd_gain property)
    """

    def __init__(
        self,
        source: Optional[RecordingSource] = None,
        rlen: Optional[int] = None,
        trig: Optional[RecTrigMode] = None,
        loop: Optional[bool] = None,
        fin: Optional[int] = None,
        fout: Optional[int] = None,
        ab_gain: Optional[int] = None,
        qrec: Optional[QRecMode] = None,
        qpl: Optional[int] = None,
        cd_gain: Optional[int] = None,
    ):
        """
        Create a RecorderSetup with optional parameter overrides.

        All parameters default to octapy defaults if not specified.

        Args:
            source: Recording source (track, input, or main)
            rlen: Recording length in steps (1-63, or 64 for MAX)
            trig: Recording trigger mode
            loop: Whether recording loops
            fin: Fade in duration (raw value)
            fout: Fade out duration (raw value)
            ab_gain: Input gain for AB (0-127)
            qrec: Quantize recording start mode
            qpl: Quantize playback mode (raw value)
            cd_gain: Input gain for CD (0-127)
        """
        # Initialize with octapy defaults
        self._data = bytearray(OCTAPY_DEFAULT_RECORDER_SETUP)

        # Apply any overrides
        if source is not None:
            self.source = source
        if rlen is not None:
            self.rlen = rlen
        if trig is not None:
            self.trig = trig
        if loop is not None:
            self.loop = loop
        if fin is not None:
            self.fin = fin
        if fout is not None:
            self.fout = fout
        if ab_gain is not None:
            self.ab_gain = ab_gain
        if qrec is not None:
            self.qrec = qrec
        if qpl is not None:
            self.qpl = qpl
        if cd_gain is not None:
            self.cd_gain = cd_gain

    @classmethod
    def read(cls, data: bytes) -> "RecorderSetup":
        """
        Read a RecorderSetup from binary data.

        Args:
            data: At least RECORDER_SETUP_SIZE (12) bytes

        Returns:
            RecorderSetup instance with data copied from input
        """
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:RECORDER_SETUP_SIZE])
        return instance

    def write(self) -> bytes:
        """
        Write this RecorderSetup to binary data.

        Returns:
            RECORDER_SETUP_SIZE (12) bytes
        """
        return bytes(self._data)

    def clone(self) -> "RecorderSetup":
        """
        Create a copy of this RecorderSetup.

        Returns:
            New RecorderSetup with copied data
        """
        instance = RecorderSetup.__new__(RecorderSetup)
        instance._data = bytearray(self._data)
        return instance

    # === Unified Source Property ===

    @property
    def source(self) -> RecordingSource:
        """
        Get/set the recording source.

        This is a unified property that abstracts over IN_AB, IN_CD, and SRC3.
        Only one source can be active at a time.

        Returns the currently active source, or OFF if all sources are disabled.
        """
        in_ab = self._data[RecorderSetupOffset.IN_AB]
        in_cd = self._data[RecorderSetupOffset.IN_CD]
        src3 = self._data[RecorderSetupOffset.SRC3]

        # Check SRC3 first (internal track sources and MAIN)
        if src3 == 9:
            return RecordingSource.MAIN
        if src3 > 0 and src3 <= 8:
            return RecordingSource(10 + src3)  # TRACK_1=11, TRACK_2=12, etc.

        # Check IN_AB (external inputs A/B)
        if in_ab > 0:
            return RecordingSource(in_ab)  # INPUT_AB=1, INPUT_A=2, INPUT_B=3

        # Check IN_CD (external inputs C/D)
        if in_cd > 0:
            return RecordingSource(3 + in_cd)  # INPUT_CD=4, INPUT_C=5, INPUT_D=6

        return RecordingSource.OFF

    @source.setter
    def source(self, value: RecordingSource):
        """Set the recording source, zeroing out unused source parameters."""
        value = RecordingSource(value)

        # Zero all source parameters first
        self._data[RecorderSetupOffset.IN_AB] = 0
        self._data[RecorderSetupOffset.IN_CD] = 0
        self._data[RecorderSetupOffset.SRC3] = 0

        if value == RecordingSource.OFF:
            return

        # Set the appropriate parameter based on source type
        if value in (RecordingSource.INPUT_AB, RecordingSource.INPUT_A,
                     RecordingSource.INPUT_B):
            # Maps to IN_AB: INPUT_AB=1, INPUT_A=2, INPUT_B=3
            self._data[RecorderSetupOffset.IN_AB] = int(value)

        elif value in (RecordingSource.INPUT_CD, RecordingSource.INPUT_C,
                       RecordingSource.INPUT_D):
            # Maps to IN_CD: INPUT_CD=4->1, INPUT_C=5->2, INPUT_D=6->3
            self._data[RecorderSetupOffset.IN_CD] = int(value) - 3

        elif value == RecordingSource.MAIN:
            # Maps to SRC3=9
            self._data[RecorderSetupOffset.SRC3] = 9

        elif int(value) >= 11 and int(value) <= 18:
            # Maps to SRC3: TRACK_1=11->1, TRACK_2=12->2, etc.
            self._data[RecorderSetupOffset.SRC3] = int(value) - 10

    # === Setup Page 1 Properties ===

    @property
    def rlen(self) -> int:
        """
        Get/set recording length in steps.

        Values 1-63 are actual step counts. Value 64 means MAX (record
        for maximum available time based on buffer size).

        Note: OT display is 1-indexed, so stored value 15 displays as 16.
        """
        return self._data[RecorderSetupOffset.RLEN]

    @rlen.setter
    def rlen(self, value: int):
        self._data[RecorderSetupOffset.RLEN] = value & 0x7F

    @property
    def trig(self) -> RecTrigMode:
        """
        Get/set recording trigger mode.

        ONE: One-shot recording for RLEN duration
        ONE2: One-shot releasable (can stop early)
        HOLD: Records while button is held
        """
        return RecTrigMode(self._data[RecorderSetupOffset.TRIG])

    @trig.setter
    def trig(self, value: RecTrigMode):
        self._data[RecorderSetupOffset.TRIG] = int(value)

    @property
    def loop(self) -> bool:
        """Get/set whether recording loops."""
        return bool(self._data[RecorderSetupOffset.LOOP])

    @loop.setter
    def loop(self, value: bool):
        self._data[RecorderSetupOffset.LOOP] = int(value)

    # === Setup Page 2 Properties ===

    @property
    def fin(self) -> int:
        """
        Get/set fade in duration.

        Raw value where display_value = raw_value / 16.0 (0-4 steps range).
        """
        return self._data[RecorderSetupOffset.FIN]

    @fin.setter
    def fin(self, value: int):
        self._data[RecorderSetupOffset.FIN] = value & 0x7F

    @property
    def fout(self) -> int:
        """
        Get/set fade out duration.

        Raw value where display_value = raw_value / 16.0 (0-4 steps range).
        Note: FOUT adds time after recording stops.
        """
        return self._data[RecorderSetupOffset.FOUT]

    @fout.setter
    def fout(self, value: int):
        self._data[RecorderSetupOffset.FOUT] = value & 0x7F

    @property
    def ab_gain(self) -> int:
        """Get/set input gain for AB (0-127)."""
        return self._data[RecorderSetupOffset.AB_GAIN]

    @ab_gain.setter
    def ab_gain(self, value: int):
        self._data[RecorderSetupOffset.AB_GAIN] = value & 0x7F

    @property
    def qrec(self) -> QRecMode:
        """
        Get/set quantize recording start mode.

        Controls when recording actually starts after being triggered.
        PLEN (0) starts at pattern loop - most useful for loops.
        OFF (255) starts immediately.
        """
        return QRecMode(self._data[RecorderSetupOffset.QREC])

    @qrec.setter
    def qrec(self, value: QRecMode):
        self._data[RecorderSetupOffset.QREC] = int(value)

    @property
    def qpl(self) -> int:
        """
        Get/set quantize playback mode.

        Same encoding as qrec. 255 = OFF.
        """
        return self._data[RecorderSetupOffset.QPL]

    @qpl.setter
    def qpl(self, value: int):
        self._data[RecorderSetupOffset.QPL] = value & 0xFF

    @property
    def cd_gain(self) -> int:
        """Get/set input gain for CD (0-127)."""
        return self._data[RecorderSetupOffset.CD_GAIN]

    @cd_gain.setter
    def cd_gain(self, value: int):
        self._data[RecorderSetupOffset.CD_GAIN] = value & 0x7F

    def to_dict(self) -> dict:
        """Convert recorder setup to dictionary."""
        return {
            "source": self.source.name,
            "rlen": self.rlen,
            "trig": self.trig.name,
            "loop": self.loop,
            "fin": self.fin,
            "fout": self.fout,
            "ab_gain": self.ab_gain,
            "qrec": self.qrec.name,
            "qpl": self.qpl,
            "cd_gain": self.cd_gain,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecorderSetup":
        """
        Create a RecorderSetup from a dictionary.

        Args:
            data: Dictionary with recorder setup properties

        Returns:
            RecorderSetup instance
        """
        kwargs = {}

        if "source" in data:
            source = data["source"]
            if isinstance(source, str):
                kwargs["source"] = RecordingSource[source]
            else:
                kwargs["source"] = RecordingSource(source)

        if "rlen" in data:
            kwargs["rlen"] = data["rlen"]

        if "trig" in data:
            trig = data["trig"]
            if isinstance(trig, str):
                kwargs["trig"] = RecTrigMode[trig]
            else:
                kwargs["trig"] = RecTrigMode(trig)

        if "loop" in data:
            kwargs["loop"] = data["loop"]

        if "fin" in data:
            kwargs["fin"] = data["fin"]

        if "fout" in data:
            kwargs["fout"] = data["fout"]

        if "ab_gain" in data:
            kwargs["ab_gain"] = data["ab_gain"]

        if "qrec" in data:
            qrec = data["qrec"]
            if isinstance(qrec, str):
                kwargs["qrec"] = QRecMode[qrec]
            else:
                kwargs["qrec"] = QRecMode(qrec)

        if "qpl" in data:
            kwargs["qpl"] = data["qpl"]

        if "cd_gain" in data:
            kwargs["cd_gain"] = data["cd_gain"]

        return cls(**kwargs)

    def __eq__(self, other) -> bool:
        """Check equality based on data buffer."""
        if not isinstance(other, RecorderSetup):
            return NotImplemented
        return self._data == other._data

    def __repr__(self) -> str:
        return f"RecorderSetup(source={self.source.name}, rlen={self.rlen}, trig={self.trig.name})"
