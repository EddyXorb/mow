from collections import defaultdict
from dataclasses import dataclass, field
import os
from os.path import join, basename
from pathlib import Path
from shutil import move
import shutil
import sys
from time import sleep
import traceback
from typing import Dict, List, Callable
from exiftool import ExifToolHelper
from math import sqrt
from tqdm import tqdm
import re


from ..mow.mowtags import MowTags
from ..general.mediafile import MediaFile
from ..general.verboseprinterclass import VerbosePrinterClass


@dataclass
class TransitionTask:
    """
    index: index of Mediafile in self.toTreat
    newName: name of mediafile in new location (only basename). If None, take old name
    skip: don' execute transition if True
    skipReason: reason for skipping transition
    rewriteMetaTagsOnConverted: a transition can include a conversion, which should rewrite the meta tags of the file
    metaTags: dict with meta-tag-key : value entries to set to file
    """

    index: int
    newName: str = None
    skip: bool = False
    skipReason: str = None
    metaTags: Dict[str, str] = field(default_factory=dict)

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
    writeMetaTags: writes meta tags to Files
    filter: regex for filtering files that should only be treated (searching the complete subpath with all subfolders of the current stage)
    rewriteMetaTagsOnConverted: a transition can include a conversion, which should rewrite the meta tags of the converted file (copying the meta tags of the original file). If converter is None, this option is ignored.
    converter: function to convert files, if None, no conversion is done. Signature: (file to convert, target directory) -> (converted file (possibly with different extensions AND name, if transition Task has diffent "newName" specified), success)
    settings: contains settings given in the .mowsettings-file, such as copy_source_dir, working_dir, etc.
    """

    src: str
    dst: str
    move: bool = True
    recursive: bool = True
    verbose: bool = False
    dry: bool = False
    maintainFolderStructure: bool = True
    removeEmptySubfolders: bool = False
    writeMetaTags: bool = True
    filter: str = ""
    mediaFileFactory: Callable[[str], MediaFile] = field(
        default_factory=lambda: None
    )  # this can also be a type with its constructor, e.g. ImageFile
    rewriteMetaTagsOnConverted: bool = False
    converter: Callable[[MediaFile, str], MediaFile] = (
        None  # (file to convert, target directory) -> (converted file (possibly with different extensions)); if None, does not convert anything.
        # If defined, converter should make sure that the source mediafile is updated in case of conversion, e.g. if .ORF and .JPG are converted to .JPG and .DNG the
        # source mediafile should be updated to contain only the .ORF file (as .JPG is only moved by the converter)
        # and the result media file should be the .JPG and .DNG file.
        # In other words, the converter needs to take care of all extensions of the source mediafile, even if it does not move/convert all of them,
        # they should at least be moved to the new location.
    )
    settings: dict[str, str] = field(default_factory=dict)


class MediaTransitioner(VerbosePrinterClass):
    """
    Abstract class for transitioning a certain mediafiletype into the next stage.
    """

    # TODO: find a good solution to the problem that there is much duplication involved in copying over the input parameters to the class attributes.
    # Possible solutions:
    # 1. Use a dataclass for the input parameters and copy them over to the class attributes in the __init__ method by iterating over the fields of the dataclass. Problem: linter won't recognize the attributes of the class as they are not defined in the class itself.
    # 2. Define only one attribute containing the input. Problem: derived classes may use derived classes of TransitionerInput and I am not sure if this is nice, if I overwrite the base class init method were the attribut .input is defined by the base class of TransitionerInput.
    def __init__(self, input: TransitionerInput):
        super().__init__(input.verbose)
        self.src = os.path.abspath(input.src)
        self.dst = os.path.abspath(input.dst)
        self.current_stage = os.path.basename(self.src)
        self.input = input
        self.move = input.move
        self.recursive = input.recursive
        self.dry = input.dry
        self.mediaFileFactory = input.mediaFileFactory
        self.converter = input.converter
        self.rewriteMetaTagsOnConverted = input.rewriteMetaTagsOnConverted
        self.maintainFolderStructure = input.maintainFolderStructure
        self.removeEmptySubfolders = input.removeEmptySubfolders
        self.writeMetaTags = input.writeMetaTags
        self.filter: re.Pattern = (
            re.compile(input.filter)
            if input.filter is not None and input.filter != ""
            else None
        )
        self.settings = input.settings

        self.toTreat: List[MediaFile] = []
        self.deleteFolder = join(self.src, "deleted")

        self._performedTransition = False
        self._toTransition: List[TransitionTask] = []
        self.et = ExifToolHelper()

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
        
        self.et.terminate() # in order to avoid usage of destructor for that

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

        already_found_files = set()

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

                if mfile.pathnoext in already_found_files:
                    continue

                already_found_files.add(mfile.pathnoext)
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
        tasks = self.getSuccesfulChangedMetaTagTasksOf(tasks)

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
                    f"Skipped {str(Path(self.toTreat[task.index].pathnoext).relative_to(self.src))}: {task.skipReason}"
                )
                cnt += 1
                if cnt >= 5 and len(tasks) - 5 >= 5:
                    self.printv(
                        f'\n{"."*int(sqrt(len(tasks) - 5))}\nSkipped message "{task.skipReason}" for other {len(tasks) - 5} files.'
                    )
                    break

        self.printv(f"Finished transition. Skipped files: {skipped}")
        return skipped

    def getSuccesfulChangedMetaTagTasksOf(self, tasks: List[TransitionTask]):
        if not self.writeMetaTags:
            return tasks

        self.printv("Set meta file tags..")

        for task in tqdm(tasks):
            try:
                files = self.toTreat[task.index].getAllFileNames()

                self.add_transition_to_files_stage_history(task, files)

                if len(task.metaTags) == 0 or self.dry:
                    continue

                self.et.set_tags(
                    files,
                    task.metaTags,
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
                    f"Problem setting meta tag data {task.metaTags} with exiftool: {e}"
                )
                if len(str(self.toTreat[task.index])) > 260:
                    task.skipReason += (
                        f"Filename is too long. Exiftool supports only 260 characters."
                    )

        return self.getNonSkippedOf(tasks)

    def add_transition_to_files_stage_history(self, task, files):
        curr_stage_history = self.et.get_tags(
            files[0],
            MowTags.stagehistory,
            params=[
                "-m",
                "-L",
                "-struct",
            ],  # -struct is needed, otherwise lists are flattened by exiftool
        )[0]

        if MowTags.stagehistory in curr_stage_history:
            curr_stage_history[MowTags.stagehistory].append(self.current_stage)
        else:
            curr_stage_history[MowTags.stagehistory] = [self.current_stage]

        task.metaTags[MowTags.stagehistory] = curr_stage_history[MowTags.stagehistory]

    def doRelocationOf(self, tasks: List[TransitionTask]) -> list[MediaFile]:
        for task in tasks:
            self.relocateSingleTask(task)

        failed_tasks = len([task for task in tasks if task.skip])
        self.printv(f"Finished transition of {len(tasks) - failed_tasks} files.")
        self.printv(f"Failed Tasks: {failed_tasks}")

    def relocateSingleTask(self, task: TransitionTask):
        toTransition = self.toTreat[task.index]
        newPath = self.getNewNameFor(task)

        self.printv(
            f"{Path(str(toTransition)).relative_to(Path(self.src).parent)}    --->    {os.path.basename(self.dst)}\\...\\{os.path.basename(newPath)}"
        )
        try:
            if not self.dry:
                os.makedirs(os.path.dirname(newPath), exist_ok=True)

                if self.converter is not None:
                    self._performConversionOf(toTransition, newPath)
                else:
                    if self.move:
                        toTransition.moveTo(newPath)
                    else:
                        toTransition.copyTo(newPath)
        except Exception as e:
            task.skip = True
            task.skipReason = traceback.format_exc(e)

    def _performConversionOf(self, toTransition: MediaFile, newPath: str):
        if self.dry:
            return

        convertedFile = self.converter(toTransition, os.path.dirname(newPath))

        for file in convertedFile.getAllFileNames():
            if not os.path.exists(file):
                raise Exception(
                    f"Conversion of {toTransition} to {convertedFile} failed. Converted file {file} does not exist."
                )

        self.printv(f"Converted {toTransition} to {convertedFile}")

        if self.rewriteMetaTagsOnConverted:
            self._performMetaTagRewriteOf(toTransition, convertedFile)

        if not toTransition.empty():
            self.deleteMediaFile(toTransition)

    def deleteMediaFile(self, file: MediaFile, extensions_to_maintain: List[str] = []):
        for ext in file.extensions:
            if ext in extensions_to_maintain:
                continue

            sourceLocation = join(file.pathnoext + ext)

            if not os.path.exists(sourceLocation):
                self.printv(
                    f"File {sourceLocation} does not exist. This is a Bug. Skip deletion and Abort."
                )
                sys.exit()

            targetLocation = join(
                self.getTargetDirectory(sourceLocation, self.deleteFolder),
                basename(sourceLocation),
            )

            self.printv(f"Delete file {sourceLocation} ( ---> {self.deleteFolder})")

            if not self.dry:
                os.makedirs(os.path.dirname(targetLocation), exist_ok=True)
                move(sourceLocation, targetLocation)

        file.extensions = [
            ext for ext in file.extensions if ext in extensions_to_maintain
        ]

    def _performMetaTagRewriteOf(
        self, toTransition: MediaFile, convertedFile: MediaFile
    ):
        self.printv(
            f"Rewrite meta tags of {os.path.basename(convertedFile.pathnoext)} to {os.path.basename(toTransition.pathnoext)}"
        )

        xmptagstowrite = self.et.get_tags(str(toTransition), MowTags.all)[0]
        xmptagstowrite.pop("SourceFile")
        self.et.set_tags(
            convertedFile.getAllFileNames(),
            xmptagstowrite,
            params=["-P", "-overwrite_original", "-L", "-m"],
        )

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
