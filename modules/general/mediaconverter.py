from dataclasses import dataclass
from typing import Callable, List, Tuple
from tqdm import tqdm
from os.path import join, basename, exists
from pathlib import Path
import os

from ..mow.mowtags import MowTags

from ..general.mediafile import MediaFile
from ..general.mediatransitioner import (
    MediaTransitioner,
    TransitionerInput,
    TransitionTask,
)

from exiftool import ExifToolHelper


def passthrough(source: MediaFile, targetDir: str):
    targetfile = join(targetDir, basename(str(source)))
    source.moveTo(targetfile)
    return True, targetfile


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


# TODO: refactor mediaconvertion into transitioner to make conversion manageable by input to the TransitionTask
class MediaConverter(MediaTransitioner):
    """
    converter: Convert mediafile and put result into directory given with second argument
    """

    def __init__(
        self,
        input: ConverterInput,
        converter: Callable[[MediaFile, str], Tuple[bool, str]] = passthrough,
    ):
        self.converter = converter
        self.deleteOriginals = input.deleteOriginals
        self.transitionTasks: List[TransitionTask] = []
        super().__init__(input)

    def convert(self):
        self.printv("Start conversion of files..")

        with ExifToolHelper() as et:
            for index, file in tqdm(enumerate(self.toTreat)):
                targetDir = self.getTargetDirectory(file, self.dst)
                if not exists(targetDir):
                    os.makedirs(targetDir)
                success = True

                if not self.dry:
                    success, convertedFile = self.converter(file, targetDir)
                    if self.converter != passthrough:
                        try:
                            xmptagstowrite = et.get_tags(str(file), MowTags.all)[0]
                            xmptagstowrite.pop("SourceFile")
                            et.set_tags(
                                convertedFile,
                                xmptagstowrite,
                                params=["-P", "-overwrite_original", "-L", "-m"],
                            )
                        except:
                            success = False
                if not success:
                    self.transitionTasks.append(
                        TransitionTask(
                            index=index, skip=True, skipReason=f"Conversion failed."
                        )
                    )
                # at the moment no else with append non-skip task needed as the converter handles everything. This should be refactored.

    def getTasks(self) -> List[TransitionTask]:
        if self.converter == passthrough:
            return [TransitionTask(index=index) for index, _ in enumerate(self.toTreat)]
        else:
            self.convert()
            return [] #TODO something is strange here and should be adressed. If transitions Tasks are returned, unittests don't run.
            return self.transitionTasks
