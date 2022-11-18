from time import sleep
from ..general.mediaconverter import ConverterInput, MediaConverter
from .videofile import VideoFile
from .transcodevideo import Transcoder
from os.path import splitext, join, basename
import os


def convertVideo(
    source: VideoFile,
    target: str,
    deleteOriginals: bool = False,
    enforcePassthrough=False,
) -> bool:
    noExt, oldExt = splitext(basename(str(source)))
    newExt = ".mp4"

    convertedFilename = join(target, noExt + newExt)
    newOriginalFile = join(target, noExt + "_original" + oldExt)

    if not enforcePassthrough:
        if os.path.exists(newOriginalFile):
            print(
                f"Abort conversion of {str(source)} as target file {newOriginalFile} is already existent!"
            )
            return False

        Transcoder(str(source), convertedFilename, quality="hd", qualityvalue=22.0)()

        sleep(1)  # otherwise the following check fails
        if not os.path.exists(convertedFilename):
            return False

        source.moveTo(newOriginalFile)

        if deleteOriginals:
            os.remove(newOriginalFile)
    else:
        source.moveTo(join(target, noExt + oldExt))

    return True


class VideoConverter(MediaConverter):
    def __init__(self, input: ConverterInput):
        input.mediaFileFactory = VideoFile
        self.enforcePassthrough = input.enforcePassthrough
        super().__init__(
            input,
            converter=lambda source, target: convertVideo(
                source,
                target,
                deleteOriginals=input.deleteOriginals,
                enforcePassthrough=self.enforcePassthrough,
            ),
        )
