from typing import List
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput


class MediaTagger(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        super().__init__(input)

    def getTasks(self) -> List[TransitionTask]:
        return [TransitionTask(index) for index, _ in enumerate(self.toTreat)]