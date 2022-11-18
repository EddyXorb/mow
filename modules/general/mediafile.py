from __future__ import annotations
from typing import Callable
import os
from shutil import copyfile, move
from os.path import *
import datetime as dt

class MediaFile:
    """
    Mediadata that can be represented by multiple files having different extensions but containing roughly the same media
    e.g. a jpeg-image and it's RAW-representation.
    """

    def __init__(self, path, validExtensions):
        self.nrFiles = 1
        self.valid = True
        self.extensions = []

        splitted = os.path.splitext(path)
        self.pathnoext = splitted[0]
        self.extensions.append(splitted[1])

        if not os.path.exists(path):
            self.valid = False
            return

        if self.extensions[0] not in validExtensions:
            self.valid = False
            return

    def __str__(self):
        return self.pathnoext + self.extensions[0]

    def isValid(self) -> bool:
        return self.valid

    def _relocate(self, dst: str, relocateFunc: Callable[[str, str], str]) -> str:
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        newBaseName = os.path.splitext(dst)[0]
        for ext in self.extensions:
            relocateFunc(self.pathnoext + ext, newBaseName + ext)

        return newBaseName

    def moveTo(self, dst: str) -> MediaFile:
        """
        dst : fullpath of new file. Extension will be ignored. After the operation the objects points to the new location.
        """
        self.pathnoext = self._relocate(dst, move)
        # return self

    def copyTo(self, dst: str) -> str:
        """
        dst : fullpath of new file. Extension will be ignored. Returns new path as string.
        """
        newBaseName = self._relocate(dst, copyfile)
        return newBaseName + self.extensions[0]

    def readDateTime(self) -> dt.datetime:
        raise NotImplementedError()
