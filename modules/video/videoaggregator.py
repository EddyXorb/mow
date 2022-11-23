from typing import List

from ..general.mediatransitioner import TransitionTask
from ..video.videofile import VideoFile
from ..general.mediaaggregator import MediaAggregator, TransitionerInput

class VideoAggregator(MediaAggregator):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = VideoFile
        super().__init__(input)

    def treatTaskBasedOnRating(self, task: TransitionTask, rating: int):
        mfile: VideoFile = self.toTreat[task.index]
        match rating:
            case 1:
                mfile.moveTo(self.deleteFolder)
                task.skip = True
                task.skipReason = "deleted file based on rating."
