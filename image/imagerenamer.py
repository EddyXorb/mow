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
        move=False,
    ):
        self.src = os.path.abspath(src)
        self.dst = os.path.abspath(dst)
        self.recursive = recursive
        self.move = move
        self.skippedfiles = []
        self.treatedjpgs = []
        
        self.run()
        
        if len(self.skippedfiles) > 0:
            print("Skipped the following files: ",self.skippedfiles)

    def createDestinationDir(self):
        os.makedirs(self.dst, exist_ok=True)
        print("Created dir ", self.dst)

    def hasCorrectExtensionToBeTreated(self, file):
        fileextension = os.path.splitext(file)[1]
        return fileextension in ImageRenamer.jpgFileEndings

    def getNewFullPath(self, file: str) -> str:
        newName = join(
            self.dst, os.path.basename(ImageRenamer.getNewImageFileNameFor(file))
        )
        if os.path.exists(newName):
            print("File ", newName, " already exists. Skip this one.")
            self.skippedfiles.append(file)
            return None
        return newName

    def copyOrMoveFromTo(self, From: str, To: str):
        print(
            "Copy " if not self.recursive else "Move ",
            os.path.splitext(From)[1],
            "-File ",
            From,
            " to ",
            To,
        )

        if self.move:
            move(From, To)
        else:
            copyfile(From, To)

    def treatJpg(self, root: str, file: str, files: List[str]):
        if not os.path.exists(join(root, file)):  # could have been moved
            return
        if not self.hasCorrectExtensionToBeTreated(file):
            return

        fullpath = join(root, file)

        newName = self.getNewFullPath(fullpath)
        if newName is None:
            return

        self.copyOrMoveFromTo(fullpath, newName)
        self.treatedjpgs.append((fullpath, newName))

    def treatRaw(self, candidate: str):
        filenameonly = os.path.basename(candidate)
        splitextension = os.path.splitext(filenameonly)
        extension = splitextension[1]
        withoutextension = splitextension[0]

        if not extension in ImageRenamer.rawFileEndings:
            return

        associatedNewJpgName = None
        for name in self.treatedjpgs:
            if withoutextension in name[0]:
                associatedNewJpgName = name[1]
                break

        if associatedNewJpgName is None:
            return

        newRawName = os.path.splitext(associatedNewJpgName)[0] + extension
        self.copyOrMoveFromTo(candidate, newRawName)

    def treatJpgs(self):
        for root, _, files in os.walk(self.src):
            if root == self.dst or (not self.recursive and root != self.dst):
                continue
            for file in files:
                self.treatJpg(root, file, files)

    def treatRaws(self):
        for root, _, files in os.walk(self.src):
            if root == self.dst or (not self.recursive and root != self.dst):
                continue
            for file in files:
                self.treatRaw(join(root, file))

    def run(self):
        self.treatJpgs()
        self.treatRaws()


#%%
testfile = (
    "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\P9032695.JPG"
)

# %%
testdir = "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\test\\"
os.path.dirname(testdir)
# %%
