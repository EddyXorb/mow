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

    def getRatedMediaFileIndices(self) -> List[int]:
        tags = []
        self.printv("Check every file for rating..")
        with ExifToolHelper() as et:
            for file in tqdm(self.toTreat):
                tags += et.get_tags(str(file), "xmp:rating")

        return [
            index for index, _ in enumerate(self.toTreat) if "XMP:Rating" in tags[index]
        ]

    def prepareTransition(self):
        pass

    def getTasks(self) -> List[TransitionTask]:
        ratedIndices = self.getRatedMediaFileIndices()
        return [TransitionTask(index) for index in ratedIndices]
