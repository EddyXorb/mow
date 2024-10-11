import datetime
import shutil
from typing import List
from pathlib import Path
import os
from ..general.mediafile import MediaFile
from ..general.mediatransitioner import TransitionTask
from ..general.medafilefactories import createAnyValidMediaFile
from ..general.mediatransitioner import TransitionerInput
from ..general.mediatransitioner import MediaTransitioner


class MediaCopier(MediaTransitioner):
    """
    The first matching file ending with '_LAST' (including all of its extensions) will mark all following files as to be copied to the destination folder,
    even if other files ending with '_LAST' are present later on.
    """
    LAST_MARKER = "_LAST"

    def __init__(self, input: TransitionerInput):
        input.move = False
        input.recursive = False
        input.writeMetaTags = False
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)

        self.indexWithLAST = -1

    def _getModificationDate(self, mFile: MediaFile) -> datetime:
        return os.path.getmtime(str(mFile))

    def getIndexWithLast(self) -> int:
        for index, f in enumerate(self.toTreat):
            if f.pathnoext.endswith(self.LAST_MARKER):
                return index
        return -1

    def getTasks(self) -> List[TransitionTask]:
        self.toTreat = sorted(self.toTreat, key=self._getModificationDate)
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
        if self.indexWithLAST > -1:
            mFile = self.toTreat[self.indexWithLAST]
            newName = mFile.pathnoext
            assert newName.endswith(self.LAST_MARKER)
            newName = newName[: -len(self.LAST_MARKER)]
            self.printv(f"Rename {mFile} to {newName}.")
            if not self.dry:
                mFile.moveTo(newName)

        if self.indexWithLAST != len(self.toTreat) - 1:
            mFile = self.toTreat[-1]
            newName = mFile.pathnoext
            newName += self.LAST_MARKER
            self.printv(f"Rename {mFile} to {newName}.")
            if not self.dry:
                mFile.moveTo(newName)
