#%%
import os
from os.path import join, splitext
import datetime as dt
from typing import List, Dict
from pathlib import Path

from .imagefile import ImageFile
from .imagehelper import getExifDateFrom
from .imagefile import ImageFile
from ..general.verboseprinterclass import VerbosePrinterClass

#%%
class ImageRenamer(VerbosePrinterClass):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    """

    def getNewImageFileNameFor(file: str) -> str:
        date = getExifDateFrom(file)
        prefixDate = f"{date:%Y-%m-%d@%H%M%S}"
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
        maintainFolderStructure=True,
        dry=False,
    ):
        super().__init__(verbose)
        self.src = os.path.abspath(src)
        self.dst = os.path.abspath(dst)
        self.recursive = recursive
        self.move = move
        self.maintainFolderStructure = maintainFolderStructure
        self.dry = dry

        self.restoreOldNames = restoreOldNames
        self.skippedfiles: List[str] = []
        self.toTreat: List[ImageFile] = []
        self.oldToNewMapping: Dict[str, str] = {}  # always jpg-names
        self.treatedfiles = 0

    def __call__(self):
        self.printv("Start renaming from source ", self.src, " into ", self.dst)

        self.createDestinationDir()
        self.collectImagesToTreat()
        self.createNewNames()

        self.executeRenaming()

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
                path = Path(join(root, file))
                ifile = ImageFile(str(path))
                if not ifile.isValid():
                    continue
                self.toTreat.append(ifile)

    def createNewNames(self):
        for im in self.toTreat:
            oldJpgName = im.getJpg()
            newJpgName = self.getRenamedFileFrom(im.getJpg())
            if newJpgName is None:
                self.skippedfiles.append(oldJpgName)
                continue

            self.oldToNewMapping[oldJpgName] = newJpgName

    def executeRenaming(self):
        for im in self.toTreat:
            if im.getJpg() in self.skippedfiles:
                continue

            newName = self.oldToNewMapping[im.getJpg()]
            if self.dry:
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
            if self.fileWasAlreadyRenamed(file):
                return None

            newFileName = os.path.basename(ImageRenamer.getNewImageFileNameFor(file))
            if self.maintainFolderStructure:
                newName = join(
                    self.dst,
                    join(str(Path(file).relative_to(self.src).parent), newFileName),
                )
            else:
                newName = join(self.dst, newFileName)

        if os.path.exists(newName):
            self.printv("File", newName, "already exists.")
            return None
        
        return newName

    def fileWasAlreadyRenamed(self, file: str):
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
