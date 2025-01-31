from __future__ import annotations
from typing import Callable
import os
from shutil import copyfile, move
import datetime as dt
from pathlib import Path


class MediaFile:
    """
    Mediadata that can be represented by multiple files having different extensions but containing roughly the same media
    e.g. a jpeg-image and it's RAW-representation. Will always check for sidecar files.
    """

    def __init__(self, path, validExtensions):
        self.valid = True
        self.extensions: list[str] = []

        splitted = os.path.splitext(path)
        self.pathnoext = splitted[0]
        self.extensions.append(splitted[1])

        if not os.path.exists(path):
            self.valid = False
            return

        if self.extensions[0] not in validExtensions:
            self.valid = False
            return

        if os.path.exists(self.get_sidecar()):
            self.extensions.append(".xmp")

    def __str__(self):
        if len(self.extensions) == 0:
            return self.pathnoext
        return self.pathnoext + self.extensions[0]

    def isValid(self) -> bool:
        return self.valid

    def _relocate(self, dst: str, relocateFunc: Callable[[str, str], str]) -> str:
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        newBaseName = os.path.splitext(dst)[0]
        for ext in self.extensions:
            relocateFunc(self.pathnoext + ext, newBaseName + ext)

        return newBaseName

    def moveTo(self, dst: str):
        """
        dst : fullpath of new file. Extension will be ignored. After the operation the objects points to the new location.
        """
        self.relocationSanityCheck(pathNoExt=self.pathnoext)

        self.pathnoext = self._relocate(dst, move)

        self.relocationSanityCheck(pathNoExt=self.pathnoext)

    def copyTo(self, dst: str) -> str:
        """
        dst : fullpath of new file. Extension will be ignored. Returns new path as string.
        """
        newBaseName = self._relocate(dst, copyfile)

        self.relocationSanityCheck(pathNoExt=self.pathnoext)
        self.relocationSanityCheck(pathNoExt=os.path.splitext(dst)[0])

        return newBaseName + self.extensions[0]

    def readDateTime(self) -> dt.datetime:
        raise NotImplementedError()

    def getAllFileNames(self) -> list[Path]:
        return [Path(self.pathnoext + ext) for ext in self.extensions]

    def getDescriptiveBasenames(self) -> str:
        """
        Returns something like 'file(.jpg,.raw)'
        """
        return f"{os.path.basename(self.pathnoext)}({','.join(self.extensions)})"

    def relocationSanityCheck(self, pathNoExt):
        for ext in self.extensions:
            if not os.path.exists(pathNoExt + ext):
                raise Exception(f"Relocation of file {self.pathnoext} failed!")

    def exists(self) -> bool:
        for file in self.getAllFileNames():
            if not os.path.exists(file):
                return False
        return True

    def remove_extension(self, extension: str):
        if extension in self.extensions:
            self.extensions.remove(extension)

    def empty(self):
        return len(self.extensions) == 0

    def has_sidecar(self):
        return ".xmp" in self.extensions

    def get_sidecar(self) -> Path:
        return Path(self.pathnoext + ".xmp")
