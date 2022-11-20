from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, List
from os.path import basename, dirname
from pathlib import Path
from tqdm import tqdm

from .mediatransitioner import MediaTransitioner, TransitionerInput, TransitionTask
from ..general.medafilefactories import createAnyValidMediaFile

from exiftool import ExifToolHelper


class MediaRater(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = createAnyValidMediaFile
        input.writeXMPTags = False
        super().__init__(input)

    def prepareTransition(self):
        pass

    def getTasks(self) -> List[TransitionTask]:
        self.printv("Check every file for rating..")

        out: List[TransitionTask] = []

        with ExifToolHelper() as et:
            for index, file in tqdm(enumerate(self.toTreat)):
                try:
                    tags = et.get_tags(str(file), "xmp:rating")[0]
                    if "XMP:Rating" in tags:
                        out.append(TransitionTask(index))
                    else:
                        out.append(
                            TransitionTask.getFailed(index, "No XMP-rating found.")
                        )
                except Exception as e:
                    out.append(
                        TransitionTask.getFailed(
                            index, f"Problem during reading of rating from XMP: {e}"
                        )
                    )
        return out
