from typing import List

from ..general.medafilefactories import createAnyValidMediaFile
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput

# TODO: add logic for inserting gps data to mediafiles based on given tracks
class MediaLocalizer(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)

    def getTasks(self) -> List[TransitionTask]:
        return [TransitionTask(index) for index, _ in enumerate(self.toTreat)]
