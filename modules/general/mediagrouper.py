from dataclasses import dataclass
from typing import DefaultDict, Dict, List


from .mediatransitioner import MediaTransitioner, TansitionerInput
import os
from os.path import basename, dirname, exists, join
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict
from exiftool import ExifToolHelper
from math import sqrt

from ..general.genericmediafile import GenericMediaFile
from ..general.mediafile import MediaFile
from ..general.filenamehelper import timestampformat


@dataclass(kw_only=True)
class GrouperInput(TansitionerInput):
    """
    groupUngroupedFiles: creates group folders with prefix 'TODO_' for every mediafile that is not in a group
    separationDistanceInHours: when groupUngroupedFiles is active, will separate two iff their timestamp differs by more than this value in hours
    addMissingTimestampsToSubfolders: if mediafiles in subfolders are found which do not have a timestamp (nowhere), will add timestamp to these folders
    separationDistanceInHours: when groupUngroupedFiles is active, if time between two neighboring mediafiles is greater equal than this time in hours, they will be put into separate groups
    """

    groupUngroupedFiles = False
    addMissingTimestampsToSubfolders = False
    separationDistanceInHours = 12
    writeXMP = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MediaGrouper(MediaTransitioner):
    """
    The idea behind this transition is the following:
    A folder is a correct groupname, if it has the format 'YYYY-MM-DD@HHMMSS#' where #=Groupname, which is an arbitrary string NOT containing the char '@'.
    Every file that is directly below the src-dir is not correctly grouped. Every file that is in a some subsubfolder of src, where every folder in between
    src and the file is a valid groupname, is correctly grouped, and otherwise not.

    Example:
    src/2022-12-12@121212_Supergroup/1999-12-12@222222_Subgroup/image.jpg is correctly grouped, but neither
    src/2022-12-12@121212_Supergroup/Subgroup/image.jpg nor
    src/Supergroup/1999-12-12@222222_Subgroup/image.jpg is, so it won't be transitioned.
    """

    def __init__(self, input: GrouperInput):
        input.mediatype = GenericMediaFile
        input.maintainFolderStructure = True
        super().__init__(input)
        self.groupUngroupedFiles = input.groupUngroupedFiles
        self.addMissingTimestampsToSubfolders = input.addMissingTimestampsToSubfolders
        self.separationDistanceInHours = input.separationDistanceInHours
        self.writeXMP = input.writeXMP

    def execute(self):
        if self.groupUngroupedFiles:
            self._groupUngrouped()
        if self.addMissingTimestampsToSubfolders:
            pass

        toTransition = self._getCorrectlyGroupedFiles()

        self._printStatisticsOf(toTransition)
        self._setOptionalXMP(toTransition)
        self._moveCorrectlyGroupedOf(toTransition)

    def _printStatisticsOf(self, toTransition):
        self.printv(
            f"Found {len(toTransition.keys())} groups that were correct (YYYY-MM-DD@HHMMSS#, #=Groupname)."
        )
        for group, files in toTransition.items():
            self.printv(f"Group {group} contains {len(files)} files.")

    def _getUngroupedFiles(self) -> list[MediaFile]:
        return list(x for x in self.toTreat if dirname(str(x)) == self.src)

    def _getCorrectlyGroupedFiles(self) -> DefaultDict[str, List[MediaFile]]:
        out: DefaultDict[str, List[MediaFile]] = defaultdict(lambda: [])
        wrongSubfolders = set()

        for file in self.toTreat:
            filepath = str(file)
            parentDir = dirname(filepath)

            if parentDir == self.src:
                continue
            if parentDir in wrongSubfolders:
                continue

            isCorrect = self._isCorrectGroupSubfolder(parentDir)
            if isCorrect:
                out[basename(parentDir)].append(file)
            else:
                wrongSubfolders.add(parentDir)

        return out

    def _isCorrectGroupSubfolder(self, folderpath: str) -> bool:
        if folderpath == self.src:
            return True

        if self._isCorrectGroupName(basename(folderpath)):
            return self._isCorrectGroupSubfolder(dirname(folderpath))

        return False

    def _isCorrectGroupName(self, candidate: str) -> bool:
        if len(candidate) <= 18:
            self.printv(f"Candidate {candidate} has length <= 18 - dismissed")
            return False

        if candidate[10] != "@":
            self.printv(
                f"Candidate {candidate} does not have '@' at index 10, but {candidate[10]} - dismissed"
            )
            return False

        if "@" in candidate[11:]:
            self.printv(f"Candidate {candidate} contains '@' at index > 10 - dismissed")
            return False

        try:
            dummy = datetime.strptime(candidate[0:17], timestampformat)
            return dummy is not None
        except:
            self.printv(f"Candidate {candidate}'s timestamp is wrong - dismissed")
            return False

    def _getGroupBasedOnFirstFile(self, file: str):
        return "TODO_" + datetime.strftime(
            self._extractDatetimeFrom(file), timestampformat
        )

    def _groupUngrouped(self):
        ungrouped = self._getUngroupedFiles()
        if len(ungrouped) == 0:
            return
        ungrouped.sort(key=lambda file: self._extractDatetimeFrom(str(file)))
        groupToFiles: DefaultDict[str, List[MediaFile]] = defaultdict(lambda: [])

        self.printv("Start creating new group names..")
        currentGroup = self._getGroupBasedOnFirstFile(str(ungrouped[0]))
        lastTime = self._extractDatetimeFrom(str(ungrouped[0]))
        for file in tqdm(ungrouped):
            if (
                (self._extractDatetimeFrom(str(file)) - lastTime).total_seconds()
                / 3600.0
            ) >= self.separationDistanceInHours:
                lastTime = self._extractDatetimeFrom(str(file))
                currentGroup = self._getGroupBasedOnFirstFile(str(file))
            groupToFiles[currentGroup].append(file)

        self.printv("Move into newly created group folder..")
        for key, val in tqdm(groupToFiles.items()):
            if not self.dry:
                for file in val:
                    file.moveTo(join(self.src, key, basename(str(file))))
            self.printv(
                f"Created new group {key} with {len(val)} files "
                + "." * int(sqrt(len(val)))
            )

    def _moveCorrectlyGroupedOf(self, toTransition: DefaultDict[str, List[MediaFile]]):
        self.printv("Move correctly grouped files..")
        for group, files in tqdm(toTransition.items()):
            self.printv(f"Move group {group}..")
            for file in files:
                if str(file) in self.skippedFiles:
                    continue

                targetDir = self.getTargetDirectory(str(file))

                if not self.dry:
                    if not exists(targetDir):
                        os.makedirs(targetDir)
                    file.moveTo(join(targetDir, basename(str(file))))

    def _setOptionalXMP(self, toTransition: DefaultDict[str, List[MediaFile]]):
        if not self.writeXMP:
            return

        with ExifToolHelper() as et:
            for group, files in tqdm(toTransition.items()):
                for file in files:
                    if self.dry:
                        self.printv(
                            f"Set XMP tag dc:Description={group} for {str(file)}"
                        )
                        continue
                    try:
                        et.set_tags(
                            str(file),
                            {"XMP-dc:Description": group},
                            params=["-P", "-overwrite_original"],  # , "-v2"],
                        )
                    except:
                        self.printv(
                            f"Could not set XMP for file {str(file)}. Skip this one."
                        )
                        self.skippedFiles.add(str(file))

    def _extractDatetimeFrom(self, file: str) -> datetime:
        try:
            return datetime.strptime(basename(file)[0:17], timestampformat)
        except Exception as e:
            self.printv(
                f"Could not get time from timestamp of file {file} because of {e}"
            )
