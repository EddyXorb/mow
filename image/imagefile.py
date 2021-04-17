from __future__ import annotations
import os
import os
from shutil import copyfile, move
from typing import List


class ImageFile:
    jpgFileEndings = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    rawFileEndings = [".ORF", ".NEF"]

    def __init__(self, file):
        """
        file must be path to a jpg-file!
        """
        self.basename = None
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
        self.basename = split[0]
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
        return self.basename + self.jpgext

    def getRaw(self) -> str:
        if self.rawext is not None:
            return self.basename + self.rawext
        return None

    def moveTo(self, to: str) -> ImageFile:
        """
        to : fullpath of new file. Extension will be ignored. After the operation the objects points to new location.
        """
        newBaseName = os.path.splitext(to)[0]
        move(self.getJpg(), newBaseName + self.jpgext)
        if self.rawext is not None:
            move(self.getRaw(), newBaseName + self.rawext)
        return ImageFile(newBaseName + self.jpgext)

    def copyTo(self, to: str) -> ImageFile:
        """
        to : fullpath of new file. Extension will be ignored.
        """
        newBaseName = os.path.splitext(to)[0]
        copyfile(self.getJpg(), newBaseName + self.jpgext)
        if self.rawext is not None:
            copyfile(self.getRaw(), newBaseName + self.rawext)

        return ImageFile(newBaseName + self.jpgext)