from ..general.mediaconverter import ConverterInput, MediaConverter
from .imagefile import ImageFile


class ImageConverter(MediaConverter):
    def __init__(self, input: ConverterInput):
        input.mediaFileFactory = ImageFile
        super().__init__(input)
