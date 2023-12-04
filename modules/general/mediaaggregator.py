from dataclasses import dataclass
from typing import Dict, List, Set

from pathlib import Path
from os.path import basename, splitext
from exiftool import ExifToolHelper
from tqdm import tqdm


from ..mow.mowtags import MowTags

from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput
from .mediagrouper import MediaGrouper
from .filenamehelper import isCorrectTimestamp
from ..general.checkresult import CheckResult
from ..general.mediafile import MediaFile


@dataclass(kw_only=True)
class AggregatorInput(TransitionerInput):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    writeXMPTags: sets XMP:Source to original filename and XMP:date to creationDate
    replace: a string such as '"^[0-9].*$",""', where the part before the comma is a regex that every file will be search after and the second part is how matches should be replaced. If given will just rename mediafiles without transitioning them to next stage.
    jpgSingleSourceOfTruth: if true, will look only at jpg when processing images to determine if tags are correct
    """

    jpgSingleSourceOfTruth: bool = False


class MediaAggregator(MediaTransitioner):
    def __init__(self, input: AggregatorInput):
        super().__init__(input)

        self.toTransition: List[TransitionTask] = []

    def getAllTagRelevantFilenamesFor(self, file: MediaFile) -> List[str]:
        return file.getAllFileNames()

    def getTagsFromTasks(self) -> Dict[int, List[Dict[str, str]]]:
        """
        Returns index to tags of all files of mediafile
        """
        self.printv("Collect xmp-tags..")
        out: Dict[int, List[Dict[str, str]]] = {}

        with ExifToolHelper() as et:
            for task in tqdm(self.toTransition):
                files = self.getAllTagRelevantFilenamesFor(self.toTreat[task.index])
                try:
                    tags = et.get_tags(files, tags=MowTags.all)
                    out[task.index] = tags
                except Exception as e:
                    out[task.index] = []
                    task.skip = True
                    task.skipReason = f"Could not parse XMP-tags: {e}"

        return out

    def prepareTransition(self):
        self.checkFileNamesHaveCorrectTimestamp()

        indexToTags = self.getTagsFromTasks()
        self.checkGrouping(indexToTags)
        self.setXMPTagsToWrite(indexToTags)
        self.deleteBasedOnRating(indexToTags)

    def getTasks(self) -> List[TransitionTask]:
        self.prepareTransition()
        return self.toTransition

    def checkFileNamesHaveCorrectTimestamp(self):
        for index, file in enumerate(self.toTreat):
            filename = basename(str(file))
            if len(filename) < 17:
                result = CheckResult(
                    False, "filename is too short to contain at least the timestamp"
                )
            else:
                result = isCorrectTimestamp(basename(str(file))[0:17])

            if not result.ok:
                self.toTransition.append(TransitionTask.getFailed(index, result.error))
            else:
                self.toTransition.append(TransitionTask(index=index))

    def checkGrouping(self, indexToTags: Dict[int, List[Dict[str, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            fullpath = Path(str(self.toTreat[task.index])).parent

            result = MediaGrouper.isCorrectGroupSubfolder(
                str(fullpath), rootFolder=self.src
            )

            if not result.ok:
                task.skip = True
                task.skipReason = result.error
                continue

            result = self.isCorrectDescriptionTag(
                groupnameToTest=str(fullpath.relative_to(self.src)),
                tagDicts=indexToTags[task.index],
            )

            if not result.ok:
                task.skip = True
                task.skipReason = result.error

    def isCorrectDescriptionTag(
        self, groupnameToTest: str, tagDicts: List[Dict[str, str]]
    ):
        for tagDict in tagDicts:
            if not MowTags.description in tagDict:
                continue

            if tagDict[MowTags.description] != groupnameToTest:
                return CheckResult(
                    False,
                    error=f"XMP-Tag {MowTags.description}:'{tagDict[MowTags.description] if MowTags.description in tagDict else ''}' is not reflecting grouping of '{tagDict['SourceFile']}'",
                )

        return CheckResult(ok=True)

    def setXMPTagsToWrite(self, indexToTags: Dict[int, List[Dict[str, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            tagsDictList = indexToTags[task.index]
            result = self.setXMPTagsToWriteFor(task, tagsDictList)

            if not result.ok:
                task.skip = True
                task.skipReason = result.error

    def setXMPTagsToWriteFor(
        self, task: TransitionTask, tagsDictList: List[Dict[str, str]]
    ) -> CheckResult:
        for tag in MowTags.all:
            allValuesThisTag: Set[str] = set()
            atLeastOneMissing = False
            tagMissingForExtension = []
            actualTagValue = None

            for tagsDict in tagsDictList:
                if tag in tagsDict:
                    actualTagValue = tagsDict[tag]
                    allValuesThisTag.add(str(tagsDict[tag]))
                else:
                    atLeastOneMissing = True
                    tagMissingForExtension.append(splitext(tagsDict["SourceFile"])[1])

            if len(allValuesThisTag) == 1 and atLeastOneMissing:
                task.XMPTags[tag] = actualTagValue
            elif len(allValuesThisTag) == 0 and tag in MowTags.expected:
                return CheckResult(
                    False,
                    f"XMP tag {tag} is missing for extension(s): {','.join(tagMissingForExtension)}",
                )
            elif len(allValuesThisTag) > 1:
                return CheckResult(
                    False,
                    f"XMP-tag {tag} differs between two files that belong to the same medium",
                )

        return CheckResult(ok=True)

    def deleteBasedOnRating(self, indexToTags: Dict[int, List[Dict[str, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            if "XMP:Rating" in task.XMPTags:
                rating = task.XMPTags["XMP:Rating"]
            else:
                rating = int(indexToTags[task.index][0]["XMP:Rating"])
            if not (1 <= int(rating) <= 5):
                task.skip = True
                task.skipReason = f"rating is {rating}, which is not within 1-5 range"
                continue

            self.treatTaskBasedOnRating(task, int(rating))

    def treatTaskBasedOnRating(self, task: TransitionTask, rating: int):
        """
        rating: is between 1-5
        """
        raise NotImplementedError()
