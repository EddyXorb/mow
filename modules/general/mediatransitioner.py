from collections import defaultdict
from dataclasses import dataclass, field
import os
from os.path import join, basename
from pathlib import Path
from typing import Dict, List, Callable
from exiftool import ExifToolHelper
from math import sqrt
from tqdm import tqdm
import re

from ..general.mediafile import MediaFile
from ..general.verboseprinterclass import VerbosePrinterClass


@dataclass
class TransitionTask:
    """
    index: index of Mediafile in self.toTreat
    newName: name of mediafile in new location (only basename). If None, take old name
    skip: don' execute transition if True
    skipReason: reason for skipping transition
    XMPTags: dict with xmp-key : value entries to set to file
    """

    index: int
    newName: str = None
    skip: bool = False
    skipReason: str = None
    XMPTags: Dict[str, str] = field(default_factory=dict)

    def getFailed(index: int, reason: str) -> "TransitionTask":
        return TransitionTask(index=index, skip=True, skipReason=reason)


@dataclass(kw_only=True)
class TransitionerInput:
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    move : move files otherwise copy them
    recursive : if true, dives into every subdir to look for files
    mediaFileFactory: factory to create Mediafiles
    verbose: additional output
    dry: don't execute actual transition
    maintainFolderStructure: copy nested folders iff true
    removeEmptySubfolders: clean empty subfolders of source after transition
    writeXMPTags: writes XMP tags to Files
    filter: regex for filtering files that should only be treated (searching the complete subpath with all subfolders of the current stage)
    """

    src: str
    dst: str
    move: bool = True
    recursive: bool = True
    verbose: bool = False
    dry: bool = False
    maintainFolderStructure: bool = True
    removeEmptySubfolders: bool = False
    writeXMPTags: bool = True
    filter: str = ""
    mediaFileFactory: Callable[[str], MediaFile] = field(
        default_factory=lambda: None
    )  # this can also be a type with its constructor, e.g. ImageFile


class MediaTransitioner(VerbosePrinterClass):
    """
    Abstract class for transitioning a certain mediafiletype into the next stage.
    """

    def __init__(self, input: TransitionerInput):
        super().__init__(input.verbose)
        self.src = os.path.abspath(input.src)
        self.dst = os.path.abspath(input.dst)
        self.input = input
        self.move = input.move
        self.recursive = input.recursive
        self.dry = input.dry
        self.mediaFileFactory = input.mediaFileFactory
        self.maintainFolderStructure = input.maintainFolderStructure
        self.removeEmptySubfolders = input.removeEmptySubfolders
        self.writeXMPTags = input.writeXMPTags
        self.filter: re.Pattern = (
            re.compile(input.filter)
            if input.filter is not None and input.filter != ""
            else None
        )

        self.toTreat: List[MediaFile] = []
        self.deleteFolder = join(self.src, "deleted")

        self._performedTransition = False
        self._toTransition: List[TransitionTask] = []

    def __call__(self):
        self.printv(f"Start transition from source {self.src} into {self.dst}")
        if self.dry:
            self.printv(
                "Dry mode active. Will NOT do anything, just print what would be done."
            )

        self.createDestinationDir()
        self.toTreat = self.collectMediaFilesToTreat()

        self._toTransition = self.getTasks()
        self.performTransitionOf(self._toTransition)
        self.printSkipped(self._toTransition)
        self._performedTransition = True

        self.optionallyRemoveEmptyFolders()
        self.finalExecution()

    def finalExecution(self):
        pass

    def createDestinationDir(self):
        if os.path.isdir(self.dst):
            return
        os.makedirs(self.dst, exist_ok=True)
        self.printv(f"Created dir {self.dst}")

    def collectMediaFilesToTreat(self) -> List[MediaFile]:
        out: List[MediaFile] = []

        self.printv("Collect files..")

        for root, dirs, files in os.walk(self.src, topdown=True):
            if not self.recursive and root != self.src:
                return out
            # ignore all files in deleteFolder
            dirs[:] = [d for d in dirs if d != basename(self.deleteFolder)]

            filtermatches = 0
            for file in files:
                path = Path(join(root, file))

                if not self.filter is None:
                    if self.filter.search(str(path)) is None:
                        continue
                    else:
                        filtermatches += 1

                mfile = self.mediaFileFactory(str(path))
                if not mfile.isValid():
                    continue

                out.append(mfile)

            if not self.filter is None and filtermatches > 0:
                self.printv(f"Matched files in {root} {'.'*filtermatches}")

        self.printv(f"Collected {len(out)} files.")

        return out

    def getTargetDirectory(self, file: str, destinationFolder: str) -> str:
        if self.maintainFolderStructure:
            return join(
                destinationFolder, str(Path(str(file)).relative_to(self.src).parent)
            )
        else:
            return destinationFolder

    def removeEmptySubfoldersOf(self, pathToRemove):
        removed = []
        toRemove = os.path.abspath(pathToRemove)
        for path, _, _ in os.walk(toRemove, topdown=False):
            if path == toRemove:
                continue
            if len(os.listdir(path)) == 0:
                if not self.dry:
                    os.rmdir(path)
                removed.append(path)
        return removed

    def performTransitionOf(self, tasks: List[TransitionTask]):
        self.printv(f"Perform transition of {len(tasks)} mediafiles..")

        tasks = self.getNonSkippedOf(tasks)
        tasks = self.getNonOverwritingTasksOf(tasks)
        tasks = self.getSuccesfulChangedXMPTasksOf(tasks)

        self.doRelocationOf(tasks)

    def getNonSkippedOf(self, tasks: List[TransitionTask]):
        return [task for task in tasks if not task.skip]

    def getNonOverwritingTasksOf(self, tasks: List[TransitionTask]):
        for task in tasks:
            newName = self.getNewNameFor(task)
            if os.path.exists(newName):
                task.skip = True
                task.skipReason = f"File exists already in {newName}!"

        return self.getNonSkippedOf(tasks)

    def getNewNameFor(self, task: TransitionTask):
        mediafile = self.toTreat[task.index]
        newName = (
            task.newName
            if task.newName is not None
            else os.path.basename(str(mediafile))
        )

        newPath = join(self.getTargetDirectory(mediafile, self.dst), newName)
        return newPath

    def printSkipped(self, tasks: List[TransitionTask]):
        skipped = 0

        messageToTask = defaultdict(list)
        for task in tasks:
            if not task.skip:
                continue
            skipped += 1
            messageToTask[task.skipReason].append(task)

        for tasks in messageToTask.values():
            cnt = 0
            for task in tasks:
                self.printv(
                    f"Skipped {str(self.toTreat[task.index])}: {task.skipReason}"
                )
                cnt += 1
                if cnt >= 5 and len(tasks) - 5 >= 5:
                    self.printv(
                        f'\n{"."*int(sqrt(len(tasks) - 5))}\nSkipped message "{task.skipReason}" for other {len(tasks) - 5} files.'
                    )
                    break

        self.printv(f"Finished transition. Skipped files: {skipped}")
        return skipped

    def getSuccesfulChangedXMPTasksOf(self, tasks: List[TransitionTask]):
        if not self.writeXMPTags:
            return tasks

        self.printv("Set XMP tags..")
        with ExifToolHelper() as et:
            for task in tqdm(tasks):
                if len(task.XMPTags) == 0 or self.dry:
                    continue
                try:
                    files = self.toTreat[task.index].getAllFileNames()

                    et.set_tags(
                        files,
                        task.XMPTags,
                        params=[
                            "-P",
                            "-overwrite_original",
                            "-L",
                            "-m",
                        ],  # , "-v2"], # -L : use latin encoding for umlaute -m: Ignore minor warnings and errors
                    )

                except Exception as e:
                    task.skip = True
                    task.skipReason = (
                        f"Problem setting XMP data {task.XMPTags} with exiftool: {e}"
                    )
                    if len(str(self.toTreat[task.index])) > 260:
                        task.skipReason += f"Filename is too long. Exiftool supports only 260 characters."

        return self.getNonSkippedOf(tasks)

    def doRelocationOf(self, tasks: List[TransitionTask]):
        failed = 0
        for task in tasks:
            toTransition = self.toTreat[task.index]
            newPath = self.getNewNameFor(task)

            self.printv(
                f"{Path(str(toTransition)).relative_to(Path(self.src).parent)}    --->    {os.path.basename(self.dst)}\\...\\{os.path.basename(newPath)}"
            )
            try:
                if not self.dry:
                    if self.move:
                        toTransition.moveTo(newPath)
                    else:
                        toTransition.copyTo(newPath)
            except Exception as e:
                task.skip = True
                task.skipReason = str(e)
                failed += 1

        self.printv(f"Finished transition of {len(tasks) - failed} files.")
        self.printv(f"Failed Tasks: {failed}")

    def optionallyRemoveEmptyFolders(self):
        if self.removeEmptySubfolders:
            removed = self.removeEmptySubfoldersOf(self.src)
            self.printv(f"Removed {len(removed)} empty subfolders of {self.src}.")

    def getSkippedTasks(self):
        if self._performedTransition:
            return [task for task in self._toTransition if task.skip]
        else:
            raise Exception(
                "Cannot call getSkippedTasks before transition was actually performed!"
            )

    def getFinishedTasks(self):
        if self._performedTransition:
            return self.getNonSkippedOf(self._toTransition)
        else:
            raise Exception(
                "Cannot call getTransitionedTasks before transition was actually performed!"
            )

    def getTasks(self) -> List[TransitionTask]:
        raise NotImplementedError()
