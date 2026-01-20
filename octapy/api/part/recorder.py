"""
RecorderSetup - recorder buffer configuration per audio track.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._io import (
    PartOffset,
    RecorderSetupOffset,
    RECORDER_SETUP_SIZE,
)
from ..enums import RecordingSource, RecTrigMode, QRecMode

if TYPE_CHECKING:
    from .audio import AudioPartTrack


class RecorderSetup:
    """
    Recorder buffer configuration for an audio track.

    Each audio track has its own recorder buffer. Track N always records
    to buffer N (fixed binding), but playback is flexible - any Flex
    machine can play any buffer via slots 129-136.

    Recording configuration is stored per-Part, meaning switching Parts
    changes your recorder setup.

    Usage:
        recorder = part.track(1).recorder

        # Set recording source (unified enum)
        recorder.source = RecordingSource.TRACK_3    # Record from track 3
        recorder.source = RecordingSource.INPUT_AB   # Record from external AB

        # Configure recording behavior
        recorder.rlen = 16                # Recording length (steps)
        recorder.trig = RecTrigMode.ONE   # One-shot recording
        recorder.qrec = QRecMode.PLEN     # Quantize to pattern start
        recorder.loop = False             # Don't loop

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

    def __init__(self, part_track: "AudioPartTrack"):
        """
        Internal constructor. Access via part.track(n).recorder.

        Args:
            part_track: The AudioPartTrack this recorder belongs to.
        """
        self._part_track = part_track

    @property
    def _data(self) -> bytearray:
        """Get the bank file data."""
        return self._part_track._data

    def _offset(self) -> int:
        """Get the byte offset for this track's RecorderSetup."""
        return (
            self._part_track._part_offset() +
            PartOffset.RECORDER_SETUP +
            (self._part_track._track_num - 1) * RECORDER_SETUP_SIZE
        )

    # === Unified Source Property ===

    @property
    def source(self) -> RecordingSource:
        """
        Get/set the recording source.

        This is a unified property that abstracts over IN_AB, IN_CD, and SRC3.
        Only one source can be active at a time.

        Returns the currently active source, or OFF if all sources are disabled.
        """
        offset = self._offset()
        in_ab = self._data[offset + RecorderSetupOffset.IN_AB]
        in_cd = self._data[offset + RecorderSetupOffset.IN_CD]
        src3 = self._data[offset + RecorderSetupOffset.SRC3]

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
        offset = self._offset()
        value = RecordingSource(value)

        # Zero all source parameters first
        self._data[offset + RecorderSetupOffset.IN_AB] = 0
        self._data[offset + RecorderSetupOffset.IN_CD] = 0
        self._data[offset + RecorderSetupOffset.SRC3] = 0

        if value == RecordingSource.OFF:
            return

        # Set the appropriate parameter based on source type
        if value in (RecordingSource.INPUT_AB, RecordingSource.INPUT_A,
                     RecordingSource.INPUT_B):
            # Maps to IN_AB: INPUT_AB=1, INPUT_A=2, INPUT_B=3
            self._data[offset + RecorderSetupOffset.IN_AB] = int(value)

        elif value in (RecordingSource.INPUT_CD, RecordingSource.INPUT_C,
                       RecordingSource.INPUT_D):
            # Maps to IN_CD: INPUT_CD=4->1, INPUT_C=5->2, INPUT_D=6->3
            self._data[offset + RecorderSetupOffset.IN_CD] = int(value) - 3

        elif value == RecordingSource.MAIN:
            # Maps to SRC3=9
            self._data[offset + RecorderSetupOffset.SRC3] = 9

        elif int(value) >= 11 and int(value) <= 18:
            # Maps to SRC3: TRACK_1=11->1, TRACK_2=12->2, etc.
            self._data[offset + RecorderSetupOffset.SRC3] = int(value) - 10

    # === Setup Page 1 Properties ===

    @property
    def rlen(self) -> int:
        """
        Get/set recording length in steps.

        Values 1-63 are actual step counts. Value 64 means MAX (record
        for maximum available time based on buffer size).
        """
        return self._data[self._offset() + RecorderSetupOffset.RLEN]

    @rlen.setter
    def rlen(self, value: int):
        self._data[self._offset() + RecorderSetupOffset.RLEN] = value & 0x7F

    @property
    def trig(self) -> RecTrigMode:
        """
        Get/set recording trigger mode.

        ONE: One-shot recording for RLEN duration
        ONE2: One-shot releasable (can stop early)
        HOLD: Records while button is held
        """
        return RecTrigMode(self._data[self._offset() + RecorderSetupOffset.TRIG])

    @trig.setter
    def trig(self, value: RecTrigMode):
        self._data[self._offset() + RecorderSetupOffset.TRIG] = int(value)

    @property
    def loop(self) -> bool:
        """Get/set whether recording loops."""
        return bool(self._data[self._offset() + RecorderSetupOffset.LOOP])

    @loop.setter
    def loop(self, value: bool):
        self._data[self._offset() + RecorderSetupOffset.LOOP] = int(value)

    # === Setup Page 2 Properties ===

    @property
    def fin(self) -> int:
        """
        Get/set fade in duration.

        Raw value where display_value = raw_value / 16.0 (0-4 steps range).
        """
        return self._data[self._offset() + RecorderSetupOffset.FIN]

    @fin.setter
    def fin(self, value: int):
        self._data[self._offset() + RecorderSetupOffset.FIN] = value & 0x7F

    @property
    def fout(self) -> int:
        """
        Get/set fade out duration.

        Raw value where display_value = raw_value / 16.0 (0-4 steps range).
        Note: FOUT adds time after recording stops.
        """
        return self._data[self._offset() + RecorderSetupOffset.FOUT]

    @fout.setter
    def fout(self, value: int):
        self._data[self._offset() + RecorderSetupOffset.FOUT] = value & 0x7F

    @property
    def ab_gain(self) -> int:
        """Get/set input gain for AB (0-127)."""
        return self._data[self._offset() + RecorderSetupOffset.AB_GAIN]

    @ab_gain.setter
    def ab_gain(self, value: int):
        self._data[self._offset() + RecorderSetupOffset.AB_GAIN] = value & 0x7F

    @property
    def qrec(self) -> QRecMode:
        """
        Get/set quantize recording start mode.

        Controls when recording actually starts after being triggered.
        PLEN (0) starts at pattern loop - most useful for loops.
        OFF (255) starts immediately.
        """
        return QRecMode(self._data[self._offset() + RecorderSetupOffset.QREC])

    @qrec.setter
    def qrec(self, value: QRecMode):
        self._data[self._offset() + RecorderSetupOffset.QREC] = int(value)

    @property
    def qpl(self) -> int:
        """
        Get/set quantize playback mode.

        Same encoding as qrec. 255 = OFF.
        """
        return self._data[self._offset() + RecorderSetupOffset.QPL]

    @qpl.setter
    def qpl(self, value: int):
        self._data[self._offset() + RecorderSetupOffset.QPL] = value & 0xFF

    @property
    def cd_gain(self) -> int:
        """Get/set input gain for CD (0-127)."""
        return self._data[self._offset() + RecorderSetupOffset.CD_GAIN]

    @cd_gain.setter
    def cd_gain(self, value: int):
        self._data[self._offset() + RecorderSetupOffset.CD_GAIN] = value & 0x7F

    def to_dict(self) -> dict:
        """Convert recorder setup to dictionary for debugging."""
        return {
            "track": self._part_track._track_num,
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
