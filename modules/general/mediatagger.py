
from ..general.medafilefactories import createAnyValidMediaFile
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput


class MediaTagger(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)

    def getTasks(self) -> list[TransitionTask]:
        return [TransitionTask(index) for index, _ in enumerate(self.toTreat)]
