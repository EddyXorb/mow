import shutil
from typing import List
from pathlib import Path
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

        self.indexWithLAST = -1

    def _getName(self, mFile: MediaFile) -> bool:
        return str(mFile)

    def getIndexWithLast(self) -> int:
        for index, f in enumerate(self.toTreat):
            if f.pathnoext.endswith("_LAST"):
                return index
        return -1

    def getTasks(self) -> List[TransitionTask]:
        self.toTreat.sort(key=self._getName)
        self.indexWithLAST = self.getIndexWithLast()

        out = list(
            map(
                lambda i: TransitionTask(i),
                range(
                    self.indexWithLAST + 1 if self.indexWithLAST != -1 else 0,
                    len(self.toTreat),
                ),
            )
        )
        return out

    def finalExecution(self):
        print(f"indexWithLast: {self.indexWithLAST}")
        if self.indexWithLAST > -1:
            mFile = self.toTreat[self.indexWithLAST]
            newName = mFile.pathnoext
            assert newName.endswith("_LAST")
            newName = newName[: -len("_LAST")]
            mFile.moveTo(newName)

        if self.indexWithLAST != len(self.toTreat) - 1:
            mFile = self.toTreat[-1]
            newName = mFile.pathnoext
            newName += "_LAST"
            mFile.moveTo(newName)