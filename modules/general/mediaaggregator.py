from typing import Dict, List

from pathlib import Path
from os.path import basename, splitext
from exiftool import ExifToolHelper

from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput
from .mediagrouper import MediaGrouper
from .filenamehelper import isCorrectTimestamp
from ..general.checkresult import CheckResult


class MediaAggregator(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        super().__init__(input)

        self.toTransition: List[TransitionTask] = []
        self.expectedTags = [
            "XMP-dc:Date",
            "XMP-dc:Source",
            "XMP-dc:Description",
            "XMP:Rating",
        ]

    def getTagsFromTasks(self):
        """
        Returns index to tags of all files of mediafile
        """
        out: Dict[int, List[Dict[str, str]]] = {}

        with ExifToolHelper() as et:
            for task in self.toTransition:

                files = self.toTreat[task.index].getAllFileNames()
                try:
                    tags = et.get_tags(files, tags=self.expectedTags)
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
        self.checkExpectedXMPTags(indexToTags)
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
            result = MediaGrouper.isCorrectGroupName(
                basename(str(Path(str(self.toTreat[task.index])).parent))
            )
            if not result.ok:
                task.skip = True
                task.skipReason = result.error

    def checkExpectedXMPTags(self, indexToTags: Dict[int, List[Dict[str, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            result = self.checkExpectedXMPTagsIn(indexToTags[task.index])
            task.skip = not result.ok
            task.skipReason = result.error

    def checkExpectedXMPTagsIn(self, tagslist: List[Dict[str, str]]) -> CheckResult:
        for singleFileTags in tagslist:
            for exp in self.expectedTags:
                if exp not in singleFileTags:
                    extension = splitext(singleFileTags["SourceFile"])[1]
                    return CheckResult(
                        ok=False,
                        error=f"XMP tag {exp} is missing for extension {extension}",
                    )

        return CheckResult(ok=True)

    def deleteBasedOnRating(self, indexToTags: Dict[int, List[Dict[str, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            rating = int(indexToTags[task.index][0]["XMP:Rating"])
            if rating not in range(1, 6):
                task.skip = True
                task.skipReason = f"rating is {rating}, which is not within 1-5 range"
                continue

            self.treatTaskBasedOnRating(task, rating)

    def treatTaskBasedOnRating(self, task: TransitionTask, rating: int):
        """
        rating: is between 1-5
        """
        raise NotImplementedError()
