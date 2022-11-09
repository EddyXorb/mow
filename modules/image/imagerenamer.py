#%%
from ..general.filenamehelper import getDateTimeFileNameFor
from ..general.mediarenamer import MediaRenamer, RenamerInput

from .imagefile import ImageFile
from .imagefile import ImageFile


class ImageRenamer(MediaRenamer):
    def __init__(self, input: RenamerInput):
        input.mediatype = ImageFile
        input.filerenamer = getDateTimeFileNameFor
        super().__init__(input)
