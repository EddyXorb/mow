from ..video.videofile import VideoFile
from ..image.imagefile import ImageFile
from .mediafile import MediaFile


class GenericMediaFile(MediaFile):
    """
    An arbitrary mediafile, but restricted to supported filetypes defined in 'normal' derived mediafiles, such as image, video or audio.
    """

    supportedMediaExtensions = (
        ImageFile.supportedjpgFormats + VideoFile.supportedVideoFileEndings
    )

    def __init__(self, path):
        super().__init__(
            path,
            validExtensions=self.supportedMediaExtensions,
        )
