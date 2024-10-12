from .mediafile import MediaFile
from ..image.imagefile import ImageFile
from ..video.videofile import VideoFile


def createAnyValidMediaFile(path: str, fast_creation=False) -> MediaFile:
    candidate: MediaFile = ImageFile(path, check_for_other_extensions=not fast_creation)
    if candidate.isValid():
        return candidate

    candidate: MediaFile = VideoFile(path)
    if candidate.isValid():
        return candidate

    return candidate
