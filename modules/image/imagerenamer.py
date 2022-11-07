#%%
from ..general.filenamehelper import getDateTimeFileNameFor
from ..general.mediafilerenamer import MediaFileRenamer, RenamerInput

from .imagefile import ImageFile
from .imagefile import ImageFile


class ImageRenamer(MediaFileRenamer):
    def __init__(self, input: RenamerInput):
        input.mediatype = ImageFile
        input.filerenamer = getDateTimeFileNameFor
        super().__init__(input)
