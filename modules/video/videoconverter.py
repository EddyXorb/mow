from time import sleep

from ..general.mediatransitioner import TransitionerInput
from ..general.mediaconverter import MediaConverter
from .videofile import VideoFile
from .transcodevideo import Transcoder
from os.path import join, basename


def convertVideo(
    source: VideoFile,
    target_dir: str,
    settings: dict = None,
) -> VideoFile:
    noExt = basename(source.pathnoext)
    newExt = ".mp4"

    convertedPath = join(target_dir, noExt + newExt)

    Transcoder(str(source), convertedPath, quality="hd", qualityvalue=22.0)()

    sleep(1)  # otherwise the following check fails

    return VideoFile(convertedPath)


class VideoConverter(MediaConverter):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = VideoFile
        input.converter = convertVideo
        input.rewriteMetaTagsOnConverted = True
        super().__init__(input)
