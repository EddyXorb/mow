from .videofile import VideoFile
from ..general.filenamehelper import getDateTimeFileNameFor
from ..general.mediafile import MediaFile
from ..general.mediarenamer import MediaRenamer, RenamerInput


class VideoRenamer(MediaRenamer):
    def __init__(self, input: RenamerInput):
        input.mediaFileFactory = VideoFile
        input.filerenamer = getDateTimeFileNameFor
        super().__init__(input)
