#%%
from ..general.filenamehelper import getDateTimeFileNameFor
from ..general.mediarenamer import MediaRenamer, RenamerInput

from .imagefile import ImageFile


class ImageRenamer(MediaRenamer):
    def __init__(self, input: RenamerInput):
        input.mediaFileFactory = ImageFile
        input.filerenamer = getDateTimeFileNameFor
        super().__init__(input)
