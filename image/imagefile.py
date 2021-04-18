from __future__ import annotations
import os
import os
from shutil import copyfile, move
from typing import List, Callable


class ImageFile:
    jpgFileEndings = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    rawFileEndings = [".ORF", ".NEF"]

    def __init__(self, file):
        """
        file must be path to a jpg-file!
        """
        self.pathnoext = None
        self.jpgext = None
        self.rawext = None
        self.isvalidimagefile = True
        self.nrfiles = 0

        if not os.path.exists(file):
            self.isvalidimagefile = False
            return
        ext = os.path.splitext(file)[1]

        if ext not in ImageFile.jpgFileEndings:
            self.isvalidimagefile = False
            return

        split = os.path.splitext(os.path.abspath(file))
        self.pathnoext = split[0]
        self.jpgext = split[1]
        self.nrfiles += 1
        self.isvalidimagefile = True

        for rawExt in ImageFile.rawFileEndings:
            rawFileCandidate = os.path.splitext(file)[0] + rawExt
            if os.path.exists(rawFileCandidate):
                self.rawext = rawExt
                self.nrfiles += 1

    def isValid(self) -> bool:
        return self.isvalidimagefile

    def getJpg(self) -> str:
        return self.pathnoext + self.jpgext

    def getRaw(self) -> str:
        if self.rawext is not None:
            return self.pathnoext + self.rawext
        return None

    def _relocate(self, dst: str, relocateFunc: Callable[[str, str], str]) -> str:
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        newBaseName = os.path.splitext(dst)[0]
        relocateFunc(self.getJpg(), newBaseName + self.jpgext)
        if self.rawext is not None:
            relocateFunc(self.getRaw(), newBaseName + self.rawext)

        return newBaseName

    def moveTo(self, dst: str) -> ImageFile:
        """
        dst : fullpath of new file. Extension will be ignored. After the operation the objects points to the new location.
        """
        self.pathnoext = self._relocate(dst, move)
        return self

    def copyTo(self, dst: str) -> ImageFile:
        """
        dst : fullpath of new file. Extension will be ignored.
        """
        newBaseName = self._relocate(dst, copyfile)
        return ImageFile(newBaseName + self.jpgext)