from .audiofile import AudioFile
from ..general.filenamehelper import getDateTimeFileNameFor
from ..general.mediarenamer import MediaRenamer, RenamerInput


class AudioRenamer(MediaRenamer):
    def __init__(self, input: RenamerInput):
        input.mediaFileFactory = AudioFile
        input.filerenamer = getDateTimeFileNameFor
        input.writeXMPTags = False
        super().__init__(input)
