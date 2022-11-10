from pathlib import Path
from os.path import join, basename

from ..general.mediaconverter import ConverterInput, MediaConverter

from .imagefile import ImageFile

class ImageConverter(MediaConverter):
    def __init__(self, input: ConverterInput):
        input.mediatype = ImageFile
        super().__init__(input)
