from dataclasses import dataclass
from typing import Callable
from tqdm import tqdm
from os.path import join, basename, exists
from pathlib import Path
import os

from ..general.mediafile import MediaFile
from ..general.mediatransitioner import MediaTransitioner, TansitionerInput


def passthrough(source: MediaFile, targetDir: str):
    source.moveTo(join(targetDir, basename(str(source))))
    return True


@dataclass(kw_only=True)
class ConverterInput(TansitionerInput):
    """
    converter: takes filename to convert and destination of result file name
    maintainfolderstructure: output converted media files in the same subfolder they were in before conversion
    """

    maintainFolderStructure = True
    deleteOriginals = False
    enforcePassthrough = False

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MediaConverter(MediaTransitioner):
    """
    converter: Convert mediafile and put result into directory given with second argument
    """

    def __init__(
        self,
        input: ConverterInput,
        converter: Callable[[MediaFile, str], bool] = passthrough,
    ):
        self.converter = converter
        self.deleteOriginals = input.deleteOriginals
        self.maintainFolderStructure = input.maintainFolderStructure
        super().__init__(input)

    # can be put into base class probably
    def _getTargetDirectory(self, file: str) -> str:
        if self.maintainFolderStructure:
            return join(self.dst, str(Path(str(file)).relative_to(self.src).parent))
        else:
            return self.dst

    def execute(self):
        self.printv("Start conversion of files..")
        for file in tqdm(self.toTreat):
            targetDir = self._getTargetDirectory(file)
            if not exists(targetDir):
                os.makedirs(targetDir)
            self.printv(f"Convert {file} into folder {targetDir}..")
            success = self.converter(file, targetDir)
            if not success:
                self.printv(f"Skipped {str(file)} because conversion failed.")
                self.skippedFiles.add(file)
