from __future__ import annotations
import os
import os
from shutil import copyfile, move
from typing import List, Callable

from ..general.mediafile import MediaFile


class ImageFile(MediaFile):
    supportedjpgFormats = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    supportedRawFormats = [".ORF", ".NEF"]

    def __init__(self, file):
        """
        file must be path to a jpg-file!
        """
        super().__init__(path=file, validExtensions=self.supportedjpgFormats)
        if not self.isValid():
            return

        for rawExt in ImageFile.supportedRawFormats:
            rawFileCandidate = os.path.splitext(file)[0] + rawExt
            if os.path.exists(rawFileCandidate):
                self.extensions.append(rawExt)
                self.nrFiles += 1

    def getJpg(self) -> str:
        return self.pathnoext + self.extensions[0]

    def getRaw(self) -> str:
        if len(self.extensions) > 1:
            return self.pathnoext + self.extensions[1]
        return None

    def copyTo(self, dst: str) -> ImageFile:
        newBaseName = self._relocate(dst, copyfile)
        return ImageFile(newBaseName + self.extensions[0])
