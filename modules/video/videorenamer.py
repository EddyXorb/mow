import os
from pathlib import Path
import time

from .videofile import VideoFile

from ..general.mediafile import MediaFile
from ..general.mediafilerenamer import MediaFileRenamer


class VideoRenamer(MediaFileRenamer):
    def __init__(
        self,
        src: str,
        dst: str,
        move: bool = False,
        verbose=False,
        writeXMP=False,
    ):
        super().__init__(
            mediafilefactory=lambda file: VideoFile(file),
            src=src,
            dst=dst,
            move=move,
            verbose=verbose,
            writeXMP=writeXMP,
        )
