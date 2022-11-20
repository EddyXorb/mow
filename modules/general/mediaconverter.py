from dataclasses import dataclass
from typing import Callable, List
from tqdm import tqdm
from os.path import join, basename, exists
from pathlib import Path
import os

from ..general.mediafile import MediaFile
from ..general.mediatransitioner import (
    MediaTransitioner,
    TransitionerInput,
    TransitionTask,
)


def passthrough(source: MediaFile, targetDir: str):
    source.moveTo(join(targetDir, basename(str(source))))
    return True


@dataclass(kw_only=True)
class ConverterInput(TransitionerInput):
    """
    converter: takes filename to convert and destination of result file name
    maintainfolderstructure: output converted media files in the same subfolder they were in before conversion
    """

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
        self.transitionTasks: List[TransitionTask] = []
        super().__init__(input)

    def prepareTransition(self):
        self.printv("Start conversion of files..")
        for index, file in tqdm(enumerate(self.toTreat)):
            targetDir = self.getTargetDirectory(file)
            if not exists(targetDir):
                os.makedirs(targetDir)
            success = True
            if not self.dry:
                success = self.converter(file, targetDir)
            if not success:
                self.transitionTasks.append(
                    TransitionTask(
                        index=index, skip=True, skipReason=f"Conversion failed."
                    )
                )
            # at the moment no else with append non-skip task needed as the converter handles everything. This should be refactored.

    def getTasks(self) -> List[TransitionTask]:
        return []
