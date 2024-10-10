import os
from time import sleep

from ..general.mediatransitioner import TransitionerInput
from ..general.mediaconverter import MediaConverter
from .videofile import VideoFile
from .transcodevideo import Transcoder
from os.path import join, basename


def convertVideo(
    source: VideoFile,
    target_dir: str,
    # deleteOriginals: bool = False,
    # enforcePassthrough=False,
    # deletionFolder="",
) -> VideoFile:
    noExt = basename(source.pathnoext)
    newExt = ".mp4"

    convertedPath = join(target_dir, noExt + newExt)
    # newOriginalFile = join(target, noExt + "_original" + oldExt)

    # if not enforcePassthrough:
    # if os.path.exists(newOriginalFile):
    #     print(
    #         f"Abort conversion of {str(source)} as target file {newOriginalFile} is already existent!"
    #     )
    #     return False, ""
    # print(f"Converting {str(source)} to {convertedPath}")
    Transcoder(str(source), convertedPath, quality="hd", qualityvalue=22.0)()

    sleep(1)  # otherwise the following check fails

    # source.moveTo(newOriginalFile)

    # if deleteOriginals:
    #     source.moveTo(
    #         os.path.join(deletionFolder, os.path.basename(newOriginalFile))
    #     )

    return VideoFile(convertedPath)
    # else:
    #     targetfile = join(target, noExt + oldExt)
    #     source.moveTo(targetfile)
    #     return True, targetfile


class VideoConverter(MediaConverter):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = VideoFile
        input.converter = convertVideo
        input.rewriteMetaTagsOnConverted = True
        super().__init__(input)
