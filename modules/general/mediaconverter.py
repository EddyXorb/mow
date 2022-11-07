from typing import Callable

from ..general.mediafile import MediaFile


class MediaConverter:
    def __init__(
        self,
        src: str,
        dst: str,
        converter: Callable[[str]],
        mediafilefactory: Callable[[str], MediaFile],
    ):
        self.src = src
        self.dst = dst
        self.converter = converter
        self.mediafilefactory = mediafilefactory

    def __call__():
        pass

    def collectMediaDataToTreat(self):
        pass
