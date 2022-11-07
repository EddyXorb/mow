from .videofile import VideoFile
from ..general.filenamehelper import getDateTimeFileNameFor
from ..general.mediafile import MediaFile
from ..general.mediafilerenamer import MediaFileRenamer, RenamerInput


class VideoRenamer(MediaFileRenamer):
    def __init__(self, input: RenamerInput):
        input.mediatype = VideoFile
        input.filerenamer = getDateTimeFileNameFor
        super().__init__(input)
