from dataclasses import dataclass
import os
from os.path import join
from pathlib import Path
from typing import Dict, List, Set, Callable


from ..general.mediafile import MediaFile
from ..general.verboseprinterclass import VerbosePrinterClass


@dataclass
class TransitionTask:
    """
    index: index of Mediafile in self.toTreat
    newName: name of mediafile in new location (only basename). If None, take old name
    """

    index: int
    newName: str = None
    skip: bool = False
    skipReason: str = None


# @dataclass
# class SkippedTask:
#     index: int
#     reason: str


@dataclass(kw_only=True)
class TansitionerInput:
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for files
    move : if true, moves files, else copies them
    mediatype: Mediafiletype to be used
    verbose: additional output
    dry: don't execute actual transition
    move : move files otherwise copy them
    """

    src: str
    dst: str
    move = True
    mediaFileFactory: Callable[
        [str], MediaFile
    ] = None  # this can also be a type with its constructor, e.g. ImageFile
    recursive = True
    verbose = False
    dry = False
    maintainFolderStructure = True
    removeEmptySubfolders = False


class MediaTransitioner(VerbosePrinterClass):
    """
    Abstract class for transitioning a certain mediafiletype into the next stage.
    """

    def __init__(self, input: TansitionerInput):
        super().__init__(input.verbose)
        self.src = os.path.abspath(input.src)
        self.dst = os.path.abspath(input.dst)
        self.move = input.move
        self.recursive = input.recursive
        self.dry = input.dry
        self.mediaFileFactory = input.mediaFileFactory
        self.maintainFolderStructure = input.maintainFolderStructure
        self.removeEmptySubfolders = input.removeEmptySubfolders
        self._toTransition: List[TransitionTask] = []
        self.performedTransition = False

        self.toTreat: List[MediaFile] = []

        self.treatedfiles = 0

    def __call__(self):
        self.printv(f"Start transition from source {self.src} into {self.dst}")
        if self.dry:
            self.printv(
                "Dry mode active. Will NOT do anything, just print what would be done."
            )

        self.createDestinationDir()
        self.collectMediaFilesToTreat()

        self.prepareTransition()

        self._toTransition = self.getTransitionTasks()
        self.performTransitionOf(self._toTransition)

        self.optionallyRemoveEmptyFolders()

    def createDestinationDir(self):
        if os.path.isdir(self.dst):
            return
        os.makedirs(self.dst, exist_ok=True)
        self.printv("Created dir", self.dst)

    def collectMediaFilesToTreat(self):
        self.printv("Collect files..")
        for root, _, files in os.walk(self.src):
            if not self.recursive and root != self.src:
                return

            for file in files:
                path = Path(join(root, file))
                mfile = self.mediaFileFactory(str(path))
                if not mfile.isValid():
                    continue
                self.toTreat.append(mfile)

        self.printv(f"Collected {len(self.toTreat)} files.")

    def getTargetDirectory(self, file: str) -> str:
        if self.maintainFolderStructure:
            return join(self.dst, str(Path(str(file)).relative_to(self.src).parent))
        else:
            return self.dst

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

        for task in tasks:
            toTransition = self.toTreat[task.index]
            if task.skip:
                continue
            newName = (
                task.newName
                if task.newName is not None
                else os.path.basename(str(toTransition))
            )
            newPath = join(self.getTargetDirectory(toTransition), newName)

            if os.path.exists(newPath):
                task.skip = True
                task.skipReason = "File exists already."

            self.printv(
                f"{Path(str(toTransition)).relative_to(self.src)} -> {Path(newPath).relative_to(self.dst)}"
            )

            if not self.dry:
                if not os.path.exists(os.path.dirname(newPath)):
                    os.makedirs(os.path.dirname(newPath))
                if self.move:
                    toTransition.moveTo(newPath)
                else:
                    toTransition.copyTo(newPath)

        skipped = self.printSkipped(tasks)
        self.printv(f"Finished transition. Skipped files: {skipped}")
        self.performedTransition = True

    def printSkipped(self, tasks: List[TransitionTask]):
        skipped = 0
        for task in tasks:
            if not task.skip:
                continue
            skipped += 1
            self.printv(f"Skipped {str(self.toTreat[task.index])}: {task.skipReason}")
        return skipped

    def optionallyRemoveEmptyFolders(self):
        if self.removeEmptySubfolders:
            removed = self.removeEmptySubfoldersOf(self.src)
            self.printv(f"Removed {len(removed)} empty subfolders of {self.src}.")

    def getSkippedTasks(self):
        if self.performedTransition:
            return [task for task in self._toTransition if task.skip]
        else:
            raise Exception(
                "Cannot call getSkippedTasks before transition was actually performed!"
            )

    def getTransitionedTasks(self):
        if self.performedTransition:
            return [task for task in self._toTransition if not task.skip]
        else:
            raise Exception(
                "Cannot call getTransitionedTasks before transition was actually performed!"
            )

    def getTransitionTasks(self) -> List[TransitionTask]:
        return []

    def prepareTransition(self):
        raise NotImplementedError()
