from typing import Dict, List, Set

from pathlib import Path
from os.path import basename, splitext
from exiftool import ExifToolHelper
from tqdm import tqdm

from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput
from .mediagrouper import MediaGrouper
from .filenamehelper import isCorrectTimestamp
from ..general.checkresult import CheckResult


class MediaAggregator(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        super().__init__(input)

        self.toTransition: List[TransitionTask] = []
        self.expectedTags = [
            "XMP:Date",
            "XMP:Source",
            "XMP:Description",
            "XMP:Rating",
        ]
        self.optionalTags = ["XMP:Subject", "XMP:Label"]

    def getTagsFromTasks(self) -> Dict[int, List[Dict[str, str]]]:
        """
        Returns index to tags of all files of mediafile
        """
        self.printv("Collect xmp-tags..")
        out: Dict[int, List[Dict[str, str]]] = {}

        with ExifToolHelper() as et:
            for task in tqdm(self.toTransition):

                files = self.toTreat[task.index].getAllFileNames()
                try:
                    tags = et.get_tags(
                        files, tags=self.expectedTags + self.optionalTags
                    )
                    out[task.index] = tags
                except Exception as e:
                    out[task.index] = []
                    task.skip = True
                    task.skipReason = f"Could not parse XMP-tags: {e}"

        return out

    def prepareTransition(self):
        self.checkFileNamesHaveCorrectTimestamp()
        self.checkGrouping()

        indexToTags = self.getTagsFromTasks()
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

    def checkGrouping(self):
        for task in self.toTransition:
            if task.skip:
                continue
            groupnameToTest = basename(str(Path(str(self.toTreat[task.index])).parent))
            result = MediaGrouper.isCorrectGroupName(groupnameToTest)
            if not result.ok:
                task.skip = True
                task.skipReason = result.error

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
        for tag in self.expectedTags + self.optionalTags:
            allValuesThisTag: Set[str] = set()
            atLeastOneMissing = False
            tagMissingForExtension = []
            subjectTagList = None

            for tagsDict in tagsDictList:
                if tag in tagsDict:
                    if tag == "XMP:Subject":
                        subjectTagList = tagsDict[
                            tag
                        ]  # we need to treat this as special case as this is a list, not string
                    allValuesThisTag.add(str(tagsDict[tag]))
                else:
                    atLeastOneMissing = True
                    tagMissingForExtension.append(splitext(tagsDict["SourceFile"])[1])

            if len(allValuesThisTag) == 1 and atLeastOneMissing:
                if tag != "XMP:Subject":
                    task.XMPTags[tag] = allValuesThisTag.pop()
                else:
                    task.XMPTags[tag] = subjectTagList
            elif len(allValuesThisTag) == 0 and tag in self.expectedTags:
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
