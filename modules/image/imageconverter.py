from ..general.mediatransitioner import TransitionerInput
from ..general.mediaconverter import MediaConverter
from .imagefile import ImageFile


class ImageConverter(MediaConverter):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = ImageFile
        input.converter = None # TODO implement dng converter
        super().__init__(input)
