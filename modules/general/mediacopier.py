from typing import List
from ..general.mediafile import MediaFile
from ..general.mediatransitioner import TransitionTask
from ..general.medafilefactories import createAnyValidMediaFile
from ..general.mediatransitioner import TransitionerInput
from ..general.mediatransitioner import MediaTransitioner


class MediaCopier(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        input.move = False
        input.recursive = False
        input.writeXMPTags = False
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)

    def _getName(self, mFile: MediaFile) -> bool:
        return str(mFile)

    def getTasks(self) -> List[TransitionTask]:
        self.toTreat.sort(key=self._getName)
        for f in self.toTreat:
            print(f)
