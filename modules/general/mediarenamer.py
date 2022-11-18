from dataclasses import dataclass
import os
from os.path import join
from typing import Callable, Dict
from pathlib import Path
from datetime import datetime

from .mediatransitioner import MediaTransitioner, TansitionerInput
from .filenamehelper import (
    getDateTimeFileNameFor,
    getMediaCreationDateFrom,
    timestampformat,
)
from tqdm import tqdm


@dataclass(kw_only=True)
class RenamerInput(TansitionerInput):
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

    move = True
    writeXMP = False
    restoreOldNames = False
    filerenamer: Callable[[str], str] = None
    useCurrentFilename = False

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MediaRenamer(MediaTransitioner):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    writeXMP: sets XMP-dc:Source to original filename and XMP-dc:date to creationDate
    useCurrentFilename: file will only be moved/copied, not renamed again, and use filename as source of truth for XMP
    """

    def __init__(self, input: RenamerInput):
        super().__init__(input)
        if input.mediaFileFactory is None:
            raise Exception("Mediatype was not given to MediaRenamer!")
        if input.filerenamer is None:
            raise Exception("Filerenamer was not given to MediaRenamer!")

        self.move = input.move
        self.renamer = input.filerenamer
        self.writeXMP = input.writeXMP
        self.restoreOldNames = input.restoreOldNames
        self.useCurrentFilename = input.useCurrentFilename

        self.oldToNewMapping: Dict[
            str, str
        ] = {}  # always a string representation of mediafiles

    def execute(self):
        self.createNewNames()
        self.addOptionalXMPData()

        self.executeRenaming()

        self.printStatistic()

    def addOptionalXMPData(self):
        if not self.writeXMP:
            return

        self.printv("Add XMP-metadata to files..")
        from exiftool import ExifToolHelper

        with ExifToolHelper() as et:
            oldfiles = list(self.oldToNewMapping.keys())
            for file in tqdm(oldfiles):
                filename = os.path.basename(file)
                if self.useCurrentFilename:
                    creationDate = datetime.strptime(
                        filename[0:17], timestampformat
                    ).strftime("%Y:%m:%d %H:%M:%S")
                else:
                    creationDate = getMediaCreationDateFrom(file).strftime(
                        "%Y:%m:%d %H:%M:%S"
                    )
                try:
                    et.set_tags(
                        file,
                        {"XMP-dc:Date": creationDate, "XMP-dc:Source": filename},
                        params=["-P", "-overwrite_original"],  # , "-v2"],
                    )
                except Exception as e:
                    print(
                        e,
                        f"Problem setting XMP data to file {file} with exiftool. Skip this one.",
                    )
                    self.skippedFiles.add(file)
                    self.oldToNewMapping.pop(file)

        self.printv("Added XMP metadata to files to rename.")

    def createNewNames(self):
        self.printv("Create new names for files..")
        for file in tqdm(self.toTreat):
            oldName = str(file)
            newName = self.getRenamedFileFrom(oldName)
            if newName is None:
                self.skippedFiles.add(oldName)
                continue
            if os.path.exists(newName):
                self.printv(f"New filename {newName} exists already. Skip this one.")
                self.skippedFiles.add(oldName)
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

        self.printv("Finished renaming files.")

    def getRenamedFileFrom(self, file: str) -> str:
        newName = ""

        if self.restoreOldNames:
            splitted = os.path.basename(file).split("_")
            if len(splitted) != 2:
                return None
            newName = join(self.dst, splitted[1])
        else:
            if not self.useCurrentFilename and self.fileWasAlreadyRenamed(file):
                self.printv(
                    f"Skip file {file} because it appears to be already renamed."
                )
                self.skippedFiles.add(file)
                return None

            newFileName = ""
            if self.useCurrentFilename:
                newFileName = os.path.basename(file)
            else:
                renamed = self.renamer(file)
                newFileName = os.path.basename(renamed)

            newName = join(self.getTargetDirectory(str(file)), newFileName)

        return newName

    def fileWasAlreadyRenamed(self, file: str):
        if "_" in file and "@" in file:
            return True
        return False

    def printStatistic(self):
        self.printv("Finished!", "Renamed", self.treatedfiles, "files.")

        if len(self.skippedFiles) > 0:
            self.printv(
                "Skipped the following files (could be due to file being already renamed (containing timestamp and _) in filename or because target existed already): "
            )
            for file in self.skippedFiles:
                self.printv(file)
