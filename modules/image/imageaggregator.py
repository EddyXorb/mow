from ..general.mediatransitioner import TransitionTask, TransitionerInput
from ..image.imagefile import ImageFile
from ..general.mediaaggregator import MediaAggregator

import os


class ImageAggregator(MediaAggregator):
    def __init__(self, input: TransitionerInput, jpgSingleSourceOfTruth: bool = False):
        """
        jpgSingleSourceOfTruth: if true, will look only at jpg when processing images to determine if tags are correct
        """
        input.mediaFileFactory = ImageFile
        self.jpgSingleSourceOfTruth = jpgSingleSourceOfTruth
        super().__init__(input)

    def getAllTagRelevantFilenamesFor(self, file: ImageFile) -> list[str]:
        return (
            [file.getJpg()]
            if self.jpgSingleSourceOfTruth
            else super().getAllTagRelevantFilenamesFor(file)
        )

    def treatTaskBasedOnRating(self, task: TransitionTask, rating: int):
        mfile: ImageFile = self.toTreat[task.index]
        match rating:
            case 1:
                self.deleteMediaFile(mfile)

                task.skip = True
                task.skipReason = "deleted file based on rating."
            case 2 | 3:
                rawfile = mfile.getRaw()
                if rawfile is None:
                    return

                self.deleteMediaFile(
                    mfile, extensions_to_maintain=os.path.splitext(mfile.getJpg())[1]
                )
