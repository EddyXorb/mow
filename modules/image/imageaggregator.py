from typing import List

from ..general.mediatransitioner import TransitionTask
from ..image.imagefile import ImageFile
from ..general.mediaaggregator import MediaAggregator, TransitionerInput

from shutil import move
from os.path import basename, join


class ImageAggregator(MediaAggregator):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = ImageFile
        super().__init__(input)

    def treatTaskBasedOnRating(self, task: TransitionTask, rating: int):
        mfile: ImageFile = self.toTreat[task.index]
        match rating:
            case 1:
                mfile.moveTo(self.deleteFolder)
                task.skip = True
                task.skipReason = "deleted file based on rating."
            case [2, 3]:

                rawfile = mfile.getRaw()
                if rawfile is None:
                    return
                target = join(
                    self.getTargetDirectory(rawfile, self.deleteFolder),
                    basename(rawfile),
                )
                move(rawfile, target)

                mfile = ImageFile(str(mfile))
