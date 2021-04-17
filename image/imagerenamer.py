#%%
from image.imagehelper import getExifDateFrom

import os
from os.path import join, splitext
import datetime as dt
from shutil import copyfile, move
from typing import List

#%%
class ImageRenamer:
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    """

    jpgFileEndings = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    rawFileEndings = [".ORF", ".NEF"]

    def getNewImageFileNameFor(file: str) -> str:
        date = getExifDateFrom(file)
        prefixDate = f"{date:%Y-%m-%d.T.%H.%M.%S}"
        return os.path.join(
            os.path.dirname(file), prefixDate + "_" + os.path.basename(file)
        )

    def __init__(
        self,
        src: str,
        dst: str,
        recursive: bool = True,
        move: bool = False,
        restoreOldNames=False,
        verbose=False,
    ):
        self.src = os.path.abspath(src)
        self.dst = os.path.abspath(dst)
        self.recursive = recursive
        self.move = move
        self.verbose = verbose
        self.restoreOldNames = restoreOldNames
        self.skippedfiles = []
        self.treatedfiles = 0

        self.printIfVerbose("Start renaming from source ", self.src, " into ", self.dst)

        self.createDestinationDir()
        self.treatImages()

        print("Finished!", "Renamed", self.treatedfiles, "files")

        if len(self.skippedfiles) > 0:
            print(
                "Skipped the following files (could be due to file being already renamed (containing timestamp and _) in filename or because target existed already): "
            )
            for file in self.skippedfiles:
                print(file)

    def printIfVerbose(self, *s):
        if self.verbose:
            print(*s)

    def createDestinationDir(self):
        if os.path.isdir(self.dst):
            return
        os.makedirs(self.dst, exist_ok=True)
        self.printIfVerbose("Created dir ", self.dst)

    def treatImages(self):
        for root, _, files in os.walk(self.src):
            if root == self.dst or (not self.recursive and root != self.src):
                continue
            print(root)
            for file in files:
                self.treat(root, file, files)

    def treat(self, root: str, file: str, files: List[str]):
        if not os.path.exists(join(root, file)):  # could have been moved
            return

        fileextension = os.path.splitext(file)[1]
        if not fileextension in ImageRenamer.jpgFileEndings:
            return

        if "_" in file and ".T." in file:
            self.printIfVerbose(
                "Skip file ",
                file,
                "because it contains underscore and '.T.' . Maybe you already renamed it?",
            )
            self.skippedfiles.append(join(root, file))
            return

        print("Treat", root, file)

        absPathJpg = join(root, file)
        newName = self.getNewAbsPathOf(absPathJpg)
        if newName is None:
            return

        self.copyOrMoveFromTo(absPathJpg, newName)
        self.treatedfiles += 1

        rawfile = ImageRenamer.getAssociatedRawFileOf(root, file, files)
        if rawfile is not None:
            self.copyOrMoveFromTo(
                rawfile, os.path.splitext(newName)[0] + os.path.splitext(rawfile)[1]
            )
            self.treatedfiles += 1

    def getNewAbsPathOf(self, file: str) -> str:
        newName = ""
        if self.restoreOldNames:
            splitted = os.path.basename(file).split("_")
            if len(splitted) != 2:
                return None
            newName = join(self.dst, splitted[1])
        else:
            newName = join(
                self.dst, os.path.basename(ImageRenamer.getNewImageFileNameFor(file))
            )

        if os.path.exists(newName):
            self.printIfVerbose("File", newName, "already exists. Skip this one.")
            self.skippedfiles.append(file)
            return None
        return newName

    def copyOrMoveFromTo(self, From: str, To: str):
        self.printIfVerbose(
            "Copy" if not self.move else "Move",
            os.path.splitext(From)[1] + "-File",
            From,
            "to",
            To,
        )

        if self.move:
            move(From, To)
        else:
            copyfile(From, To)

    def getAssociatedRawFileOf(root: str, file: str, files: List[str]):
        basenameJpg = file
        for f in files:
            if (
                os.path.splitext(f)[0] == os.path.splitext(basenameJpg)[0]
                and basenameJpg != f
                and os.path.splitext(f)[1] in ImageRenamer.rawFileEndings
            ):
                return join(root, f)
        return None
