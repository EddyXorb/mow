import os
from os.path import join, splitext
import datetime as dt
from typing import List, Dict
from pathlib import Path

from ..general.mediafile import MediaFile
from .filenamehelper import getDateTimeFileNameFor, getMediaCreationDateFrom
from ..general.verboseprinterclass import VerbosePrinterClass
from tqdm import tqdm
from typing import Callable

#%%
class MediaFileRenamer(VerbosePrinterClass):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    writeXMP: sets XMP-dc:Source to original filename and XMP-dc:date to creationDate
    """

    def __init__(
        self,
        src: str,
        dst: str,
        mediafilefactory: Callable[
            [str], MediaFile
        ],  # creates mediafile from path to file
        filerenamer: Callable[
            [str], str
        ] = getDateTimeFileNameFor,  # creates new filename from path to file
        recursive: bool = True,
        move: bool = False,
        restoreOldNames=False,
        verbose=False,
        maintainFolderStructure=True,
        dry=False,
        writeXMP=False,
    ):
        super().__init__(verbose)
        self.mediafilefactory = mediafilefactory
        self.renamer = filerenamer

        self.src = os.path.abspath(src)
        self.dst = os.path.abspath(dst)
        self.recursive = recursive
        self.move = move
        self.maintainFolderStructure = maintainFolderStructure
        self.dry = dry
        self.writeXMP = writeXMP

        self.restoreOldNames = restoreOldNames
        self.skippedFiles: List[str] = []
        self.toTreat: List[MediaFile] = []
        self.oldToNewMapping: Dict[
            str, str
        ] = {}  # always a string representation of mediafiles
        self.treatedfiles = 0

    def __call__(self):
        self.printv("Start renaming from source ", self.src, " into ", self.dst)

        self.createDestinationDir()
        self.collectMediaFilesToTreat()
        self.createNewNames()
        self.addOptionalXMPData()

        self.executeRenaming()

        self.printStatistic()

    def createDestinationDir(self):
        if os.path.isdir(self.dst):
            return
        os.makedirs(self.dst, exist_ok=True)
        self.printv("Created dir ", self.dst)

    def collectMediaFilesToTreat(self):
        self.printv("Collect files to rename..")
        for root, _, files in os.walk(self.src):
            if not self.recursive and root != self.src:
                continue

            for file in files:
                path = Path(join(root, file))
                mfile = self.mediafilefactory(str(path))
                if not mfile.isValid():
                    continue
                self.toTreat.append(mfile)

        self.printv(f"Collected {len(self.toTreat)} files for renaming.")

    def addOptionalXMPData(self):
        if not self.writeXMP:
            return

        self.printv("Add XMP-metadata to files..")
        from exiftool import ExifToolHelper

        with ExifToolHelper() as et:
            oldfiles = list(self.oldToNewMapping.keys())
            for file in tqdm(oldfiles):
                filename = os.path.basename(file)
                creationDate = getMediaCreationDateFrom(file).strftime(
                    "%Y:%m:%d %H:%M:%S"
                )
                try:
                    done = et.set_tags(
                        file,
                        {"XMP-dc:Date": creationDate, "XMP-dc:Source": filename},
                        params=["-P", "-overwrite_original"],  # , "-v2"],
                    )
                except Exception as e:
                    print(
                        e,
                        f"Problem setting XMP data to file {file} with exiftool. Skip this one.",
                    )
                    self.skippedFiles.append(file)
                    self.oldToNewMapping.pop(file)

        self.printv("Added XMP metadata to files to rename.")

    def createNewNames(self):
        self.printv("Create new names for files..")
        for file in tqdm(self.toTreat):
            oldName = str(file)
            newName = self.getRenamedFileFrom(oldName)
            if newName is None:
                self.skippedFiles.append(oldName)
                continue
            if os.path.exists(newName):
                print(f"New filename {newName} exists already. Skip this one.")
                self.skippedFiles.append(oldName)
                continue

            self.oldToNewMapping[oldName] = newName

        self.printv("Created new names for files..")

    def executeRenaming(self):
        self.printv("Execute renaming..")
        for file in tqdm(self.toTreat):
            if str(file) in self.skippedFiles:
                continue

            newName = self.oldToNewMapping[str(file)]
            if self.dry:
                continue

            if self.move:
                file.moveTo(newName)
            else:
                file.copyTo(newName)

            self.treatedfiles += file.nrFiles

        self.printv("Finshed renaming files.")

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

            renamed = self.renamer(file)
            newFileName = os.path.basename(renamed)

            if self.maintainFolderStructure:
                newName = join(
                    self.dst,
                    join(str(Path(file).relative_to(self.src).parent), newFileName),
                )
            else:
                newName = join(self.dst, newFileName)

        return newName

    def fileWasAlreadyRenamed(self, file: str):
        if "_" in file and "@" in file:
            self.printv(
                "Skip file ",
                file,
                "because it contains underscore and '@' . Maybe you already renamed it?",
            )
            self.skippedFiles.append(file)
            return True
        return False

    def printStatistic(self):
        print("Finished!", "Renamed", self.treatedfiles, "files.")

        if len(self.skippedFiles) > 0:
            print(
                "Skipped the following files (could be due to file being already renamed (containing timestamp and _) in filename or because target existed already): "
            )
            for file in self.skippedFiles:
                print(file)
