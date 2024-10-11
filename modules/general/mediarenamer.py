from dataclasses import dataclass
import os
from os.path import join
from typing import Callable, Dict, List, Tuple
from pathlib import Path
from datetime import datetime
import re

from .mediatransitioner import MediaTransitioner, TransitionerInput, TransitionTask

from .filenamehelper import getMediaCreationDateFrom, timestampformat
from tqdm import tqdm


@dataclass(kw_only=True)
class RenamerInput(TransitionerInput):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    writeMetaTags: sets XMP:Source to original filename and XMP:date to creationDate
    replace: a string such as '"^[0-9].*$",""', where the part before the comma is a regex that every file will be search after and the second part is how matches should be replaced. If given will just rename mediafiles without transitioning them to next stage.
    """

    restoreOldNames: bool = False
    filerenamer: Callable[[str], str] = None
    useCurrentFilename: bool = False
    replace: str = ""


class MediaRenamer(MediaTransitioner):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    writeMetaTags: sets XMP:Source to original filename and XMP:date to creationDate
    useCurrentFilename: file will only be moved/copied, not renamed again, and use filename as source of truth for XMP
    """

    def __init__(self, input: RenamerInput):
        super().__init__(input)
        if input.mediaFileFactory is None:
            raise Exception("Mediatype was not given to MediaRenamer!")
        if input.filerenamer is None:
            raise Exception("Filerenamer was not given to MediaRenamer!")

        self.replace: str = input.replace
        self.transitionTasks: List[TransitionTask] = []

        self.replace = self.initReplace(input.replace)

    def initReplace(self, input: str) -> str:
        if "," in input and len(input.split(",")) == 2:
            self.printv(f"Found replace pattern {self.replace}!")
            return input
        elif input != "":
            self.printv(f"Given replace pattern {self.replace} is invalid.")
        return None

    def prepareTransition(self):
        if self.replace is not None:
            self.performReplacement()
            return

        self.createNewNames()
        self.setXMPTags()

    def performReplacement(self):
        regex, replacing = self.replace.split(",")
        for file in self.toTreat:
            name, ext = os.path.splitext(os.path.basename(str(file)))
            newFileName = re.sub(regex, replacing, name)
            if newFileName == name:
                continue
            newFullPath = join(os.path.dirname(str(file)), newFileName + ext)
            if not self.dry:
                file.moveTo(newFullPath)
            self.printv(
                f"Replaced {Path(str(file)).relative_to(self.src)}    --->    {newFileName}{ext}"
            )

    def getTasks(self) -> List[TransitionTask]:
        self.prepareTransition()
        return self.transitionTasks

    def setXMPTags(self):
        if not self.writeMetaTags:
            return

        for task in tqdm(self.transitionTasks):
            if task.skip:
                continue

            mediafile = self.toTreat[task.index]
            filename = os.path.basename(str(mediafile))

            if self.input.useCurrentFilename:
                creationDate = datetime.strptime(
                    filename[0:17], timestampformat
                ).strftime("%Y:%m:%d %H:%M:%S")
            else:
                creationDate = getMediaCreationDateFrom(str(mediafile)).strftime(
                    "%Y:%m:%d %H:%M:%S"
                )

            task.metaTags = {"XMP:Date": creationDate, "XMP:Source": filename}

    def createNewNames(self):
        self.printv("Create new names for files..")

        for index, file in tqdm(enumerate(self.toTreat)):
            oldName = str(file)
            newName, errorreason = self.getRenamedFileFrom(oldName)

            if newName is None:
                self.transitionTasks.append(
                    TransitionTask(
                        index,
                        skip=True,
                        skipReason=f"Could not create new name: {errorreason}",
                    )
                )
                continue

            self.transitionTasks.append(
                TransitionTask(index=index, newName=os.path.basename(newName))
            )

        self.printv("Created new names for files.")

    def getRenamedFileFrom(self, file: str) -> Tuple[str, str]:  # new name, errorreason
        if self.input.restoreOldNames:
            splitted = os.path.basename(file).split("_")
            if len(splitted) != 2:
                return (
                    None,
                    "File contains not exactly one '_', which is needed for restoring old names (could be improved however).",
                )
            return splitted[1], None

        if not self.input.useCurrentFilename and self.fileWasAlreadyRenamed(file):
            return None, f"File appears to be already renamed."

        if self.input.useCurrentFilename:
            return os.path.basename(file), None

        return os.path.basename(self.input.filerenamer(file)), None

    def fileWasAlreadyRenamed(self, file: str):
        if "_" in os.path.basename(file) and "@" in os.path.basename(file):
            return True
        return False
