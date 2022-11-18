from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Tuple


from .mediatransitioner import MediaTransitioner, TansitionerInput
import os
from os.path import basename, dirname, exists, join
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict
from exiftool import ExifToolHelper
from math import sqrt
import re


from ..image.imagefile import ImageFile
from ..video.videofile import VideoFile
from ..general.mediafile import MediaFile
from ..general.filenamehelper import timestampformat


@dataclass(kw_only=True)
class GrouperInput(TansitionerInput):
    """
    automaticGrouping: creates group folders with prefix 'TODO_' for every mediafile that is not in a group
    undoAutomatedGrouping: copies all mediafiles from folders into src that are in group-like-folders with TODO_YYYY-MM-DD@HHMMSS - format
    separationDistanceInHours: when groupUngroupedFiles is active, will separate two iff their timestamp differs by more than this value in hours
    addMissingTimestampsToSubfolders: if mediafiles in subfolders without timestamp are found, will add timestamp to these folders taking the first time of files within this folder
    separationDistanceInHours: when groupUngroupedFiles is active, if time between two neighboring mediafiles is greater equal than this time in hours, they will be put into separate groups
    """

    undoAutomatedGrouping = False
    automaticGrouping = False
    addMissingTimestampsToSubfolders = False
    separationDistanceInHours = 12
    writeXMP = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def createGroupableMediaFile(path: str) -> MediaFile:
    for type in [ImageFile, VideoFile]:
        candidate: MediaFile = type(path)
        if candidate.isValid():
            return candidate

    return candidate


class MediaGrouper(MediaTransitioner):
    """
    The idea behind this transition is the following:
    A folder is a correct groupname, if it has the format 'YYYY-MM-DD@HHMMSS#' where #=Groupname, which is an arbitrary string of length >= 2 NOT containing the char '@'.
    Every file that is directly below the src-dir is not correctly grouped. Every file that is in a some subsubfolder of src, where every folder in between
    src and the file is a valid groupname, is correctly grouped, and otherwise not.

    Example:
    src/2022-12-12@121212_Supergroup/1999-12-12@222222_Subgroup/image.jpg is correctly grouped, but neither
    src/2022-12-12@121212_Supergroup/Subgroup/image.jpg nor
    src/Supergroup/1999-12-12@222222_Subgroup/image.jpg is, so it won't be transitioned.
    """

    def __init__(self, input: GrouperInput):
        input.mediaFileFactory = createGroupableMediaFile
        input.maintainFolderStructure = True
        super().__init__(input)
        self.undoAutomatedGrouping = input.undoAutomatedGrouping
        self.groupUngroupedFiles = input.automaticGrouping
        self.addMissingTimestampsToSubfolders = input.addMissingTimestampsToSubfolders
        self.separationDistanceInHours = input.separationDistanceInHours
        self.writeXMP = input.writeXMP

    def execute(self):
        if self.undoAutomatedGrouping:
            self.printv("Start undo grouping..")
            self.undoGrouping()
            return
        if self.groupUngroupedFiles:
            self.printv("Start automated grouping..")
            self.groupUngrouped()
            return
        if self.addMissingTimestampsToSubfolders:
            self.printv("Start adding missing timestamps..")
            self.addMissingTimestamps()
            return

        self.printv("Start transitioning from group stage..")
        toTransition = self.getCorrectlyGroupedFiles()

        self.printStatisticsOf(toTransition)
        self.setOptionalXMP(toTransition)
        self.moveCorrectlyGroupedOf(toTransition)

    def undoGrouping(self):
        candidatesForUndo = [
            group
            for group in os.listdir(self.src)
            if os.path.isdir(join(self.src, group))
            and group.startswith("TODO_")
            and self.isCorrectTimestamp(group[5:])
        ]

        self.printv(f"Found {len(candidatesForUndo)} groups for undo.")

        for group in candidatesForUndo:
            movedFiles = 0
            for f in os.listdir(join(self.src, group)):
                file = join(self.src, group, f)
                if not os.path.isfile(file):
                    continue
                if not os.path.exists(file):
                    continue

                toMove = createGroupableMediaFile(file)
                if not toMove.isValid():
                    continue
                if not self.dry:
                    toMove.moveTo(join(self.src, basename(str(toMove))))

                movedFiles += 1

            self.printv(
                f"Moved {movedFiles : 4} files from {group} back to {self.src}."
            )

    def getLowestDatetimeOfTimestampsIn(self, folder: str) -> datetime:
        candidates = os.listdir(folder)
        timestamps = []
        for cand in candidates:
            timestamp = self.extractDatetimeFrom(cand, verbose=False)
            if timestamp is not None:
                timestamps.append(timestamp)

        if len(timestamps) == 0:
            return None

        timestamps.sort()
        return timestamps[0]

    def addMissingTimestamps(self):
        renamed: List[Tuple(str, str)] = []
        for root, folders, files in os.walk(self.src, topdown=False):
            print(f"Looking into {root}..")
            for folder in folders:
                if "@" in folder or re.search(r"\d(\d+)-\d\d-\d\d", folder):
                    continue
                timestamp = self.getLowestDatetimeOfTimestampsIn(join(root, folder))
                if timestamp is None:
                    continue

                source = join(root, folder)
                target = join(
                    root, f"{datetime.strftime(timestamp, timestampformat)} {folder}"
                )

                self.printv(f"Rename {source} to {target}..")
                if os.path.exists(target):
                    self.printv(
                        f"Group with timestamp is already existent. Skip renaming of {source} to {target}."
                    )
                    continue
                if not self.dry:
                    os.rename(source, target)

                renamed.append((source, target))

        self.printv(
            f"Renamed {len(renamed)} folders without timestamps to folders that have one."
        )

    def printStatisticsOf(self, toTransition):
        self.printv(
            f"Found {len(toTransition.keys())} groups that were correct (YYYY-MM-DD@HHMMSS#, #=Groupname)."
        )
        for group, files in toTransition.items():
            self.printv(f"Group {group} contains {len(files)} files.")

    def getUngroupedFiles(self) -> list[MediaFile]:
        return list(x for x in self.toTreat if dirname(str(x)) == self.src)

    def getCorrectlyGroupedFiles(self) -> DefaultDict[str, List[MediaFile]]:
        out: DefaultDict[str, List[MediaFile]] = defaultdict(lambda: [])
        wrongSubfolders = set()

        for file in self.toTreat:
            filepath = str(file)
            parentDir = dirname(filepath)

            if parentDir == self.src:
                continue
            if parentDir in wrongSubfolders:
                continue

            isCorrect = self.isCorrectGroupSubfolder(parentDir)
            if isCorrect:
                out[basename(parentDir)].append(file)
            else:
                wrongSubfolders.add(parentDir)

        return out

    def isCorrectGroupSubfolder(self, folderpath: str) -> bool:
        if folderpath == self.src:
            return True

        if self.isCorrectGroupName(basename(folderpath)):
            return self.isCorrectGroupSubfolder(dirname(folderpath))

        return False

    def isCorrectTimestamp(self, candidate: str) -> bool:
        if candidate[10] != "@":
            self.printv(
                f"Candidate {candidate} does not have '@' at index 10, but {candidate[10]} - dismissed"
            )
            return False

        try:
            dummy = datetime.strptime(candidate[0:17], timestampformat)
            return dummy is not None
        except:
            self.printv(f"Candidate {candidate}'s timestamp is wrong - dismissed")
            return False

    def isCorrectGroupName(self, candidate: str) -> bool:
        if len(candidate) <= 18:
            self.printv(
                f"Candidate {candidate} has no or too short description (should at least have length 2) - dismissed"
            )
            return False

        if "@" in candidate[11:]:
            self.printv(f"Candidate {candidate} contains '@' at index > 10 - dismissed")
            return False

        return self.isCorrectTimestamp(candidate=candidate[0:17])

    def _getGroupBasedOnFirstFile(self, file: str):
        return "TODO_" + datetime.strftime(
            self.extractDatetimeFrom(file), timestampformat
        )

    def groupUngrouped(self):
        ungrouped = self.getUngroupedFiles()
        if len(ungrouped) == 0:
            return
        ungrouped.sort(key=lambda file: self.extractDatetimeFrom(str(file)))
        groupToFiles: DefaultDict[str, List[MediaFile]] = defaultdict(lambda: [])

        self.printv("Start creating new group names..")
        currentGroup = self._getGroupBasedOnFirstFile(str(ungrouped[0]))
        lastTime = self.extractDatetimeFrom(str(ungrouped[0]))
        for file in tqdm(ungrouped):
            if (
                (self.extractDatetimeFrom(str(file)) - lastTime).total_seconds()
                / 3600.0
            ) >= self.separationDistanceInHours:
                currentGroup = self._getGroupBasedOnFirstFile(str(file))
            groupToFiles[currentGroup].append(file)
            lastTime = self.extractDatetimeFrom(str(file))

        self.printv(f"Created {len(groupToFiles)} new groups.")
        self.printv("Move into newly created group folder..")
        for key, val in groupToFiles.items():
            if not self.dry:
                for file in val:
                    file.moveTo(join(self.src, key, basename(str(file))))
            self.printv(
                f"Created new group {key} with {len(val):4} files "
                + "." * int(sqrt(len(val)))
            )

    def moveCorrectlyGroupedOf(self, toTransition: DefaultDict[str, List[MediaFile]]):
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

    def setOptionalXMP(self, toTransition: DefaultDict[str, List[MediaFile]]):
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

    def extractDatetimeFrom(self, file: str, verbose=True) -> datetime:
        try:
            return datetime.strptime(basename(file)[0:17], timestampformat)
        except Exception as e:
            if verbose:
                self.printv(
                    f"Could not get time from timestamp of file {file} because of {e}"
                )
            return None
