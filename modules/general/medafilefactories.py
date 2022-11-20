from .mediafile import MediaFile
from ..image.imagefile import ImageFile
from ..video.videofile import VideoFile


def createAnyValidMediaFile(path: str) -> MediaFile:
    for type in [ImageFile, VideoFile]:
        candidate: MediaFile = type(path)
        if candidate.isValid():
            return candidate

    return candidate
