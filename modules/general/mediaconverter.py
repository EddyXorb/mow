from dataclasses import dataclass
from typing import Callable
from tqdm import tqdm
from os.path import join, basename
from pathlib import Path

from ..general.mediafile import MediaFile
from ..general.mediatransitioner import MediaTransitioner, TansitionerInput


def passthrough(source: MediaFile, target: str):
    source.moveTo(target)


@dataclass(kw_only=True)
class ConverterInput(TansitionerInput):
    """
    converter: takes filename to convert and destination of result file name
    maintainfolderstructure: output converted media files in the same subfolder they were in before conversion
    """

    maintainFolderStructure = True
    deleteOriginals = False

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MediaConverter(MediaTransitioner):
    def __init__(
        self,
        input: ConverterInput,
        converter: Callable[[MediaFile, str], None] = passthrough,
    ):
        self.converter = converter
        self.deleteOriginals = input.deleteOriginals
        self.maintainFolderStructure = input.maintainFolderStructure
        super().__init__(input)

    # can be put into base class probably
    def getConvertedFilename(self, file: str) -> str:
        if self.maintainFolderStructure:
            return join(
                self.dst,
                str(Path(str(file)).relative_to(self.src).parent),
                basename(str(file)),
            )
        else:
            return join(self.dst, basename(str(file)))

    def callconverter(self, s, t):
        self.converter(s, t)

    def execute(self):
        self.printv("Start conversion of files..")
        for file in tqdm(self.toTreat):
            conversionTarget = self.getConvertedFilename(file)
            self.converter(file, conversionTarget)
            self.printv(f"Converted {file} to {conversionTarget}.")
