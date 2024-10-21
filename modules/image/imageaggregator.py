from typing import List

from ..general.mediatransitioner import TransitionTask
from ..image.imagefile import ImageFile
from ..general.mediaaggregator import AggregatorInput, MediaAggregator

import os


class ImageAggregator(MediaAggregator):
    def __init__(self, input: AggregatorInput):
        input.mediaFileFactory = ImageFile
        self.jpgSingleSourceOfTruth = input.jpgSingleSourceOfTruth
        super().__init__(input)

    def getAllTagRelevantFilenamesFor(self, file: ImageFile) -> List[str]:
        return (
            [file.getJpg()] if self.jpgSingleSourceOfTruth else file.getAllFileNames()
        )

    def treatTaskBasedOnRating(self, task: TransitionTask, rating: int):
        mfile: ImageFile = self.toTreat[task.index]
        match rating:
            case 1:
                self.deleteMediaFile(mfile)

                task.skip = True
                task.skipReason = "deleted file based on ratist_correctImageIsTransitiong."
            case 2 | 3:
                rawfile = mfile.getRaw()
                if rawfile is None:
                    return

                self.deleteMediaFile(
                    mfile, extensions_to_maintain=os.path.splitext(mfile.getJpg())[1]
                )
