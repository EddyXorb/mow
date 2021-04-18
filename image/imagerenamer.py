#%%
import os
from os.path import join, splitext
import datetime as dt
from typing import List

from image.imagefile import ImageFile
from image.imagehelper import getExifDateFrom
from image.imagefile import ImageFile
from general.verboseprinterclass import VerbosePrinterClass

#%%
class ImageRenamer(VerbosePrinterClass):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    """

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
        super().__init__(verbose)
        self.src = os.path.abspath(src)
        self.dst = os.path.abspath(dst)
        self.recursive = recursive
        self.move = move

        self.restoreOldNames = restoreOldNames
        self.skippedfiles: List[str] = []
        self.toTreat: List[ImageFile] = []
        self.treatedfiles = 0

        self.printv("Start renaming from source ", self.src, " into ", self.dst)

        self.createDestinationDir()
        self.collectImagesToTreat()
        self.treatImages()

        self.printStatistic()

    def createDestinationDir(self):
        if os.path.isdir(self.dst):
            return
        os.makedirs(self.dst, exist_ok=True)
        self.printv("Created dir ", self.dst)

    def collectImagesToTreat(self):
        for root, _, files in os.walk(self.src):
            if not self.recursive and root != self.src:
                continue

            for file in files:
                ifile = ImageFile(join(root, file))
                if not ifile.isValid():
                    continue
                self.toTreat.append(ifile)

    def treatImages(self):
        for im in self.toTreat:

            newName = self.getRenamedFileFrom(im.getJpg())
            if newName is None:
                self.skippedfiles.append(im.getJpg())
                continue

            if self.move:
                im.moveTo(newName)
            else:
                im.copyTo(newName)

            self.treatedfiles += im.nrfiles

    def getRenamedFileFrom(self, file: str) -> str:
        newName = ""
        if self.restoreOldNames:
            splitted = os.path.basename(file).split("_")
            if len(splitted) != 2:
                return None
            newName = join(self.dst, splitted[1])
        else:
            if self.filewasalreadyrenamed(file):
                return
            newName = join(
                self.dst, os.path.basename(ImageRenamer.getNewImageFileNameFor(file))
            )

        if os.path.exists(newName):
            self.printv("File", newName, "already exists. Skip this one.")
            self.skippedfiles.append(file)
            return None

        return newName

    def filewasalreadyrenamed(self, file: str):
        if "_" in file and ".T." in file:
            self.printv(
                "Skip file ",
                file,
                "because it contains underscore and '.T.' . Maybe you already renamed it?",
            )
            self.skippedfiles.append(file)
            return True
        return False

    def printStatistic(self):
        print("Finished!", "Renamed", self.treatedfiles, "files.")

        if len(self.skippedfiles) > 0:
            print(
                "Skipped the following files (could be due to file being already renamed (containing timestamp and _) in filename or because target existed already): "
            )
            for file in self.skippedfiles:
                print(file)
