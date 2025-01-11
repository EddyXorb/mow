from dataclasses import dataclass
from typing import Dict, Set

from pathlib import Path
from os.path import basename, splitext
from rich.progress import track

from ..mow.mowtags import MowTag, MowTagFileManipulator, tags_all, tags_expected
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput
from .mediagrouper import MediaGrouper
from .filenamehelper import isCorrectTimestamp
from ..general.checkresult import CheckResult
from ..general.mediafile import MediaFile


class MediaAggregator(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        super().__init__(input)
        self.toTransition: list[TransitionTask] = []

    def getAllTagRelevantFilenamesFor(self, file: MediaFile) -> list[Path]:
        return file.getAllFileNames()

    def getTagsFromTasks(self) -> dict[int, list[dict[MowTag, str]]]:
        """
        Returns index to tags of all files of mediafile
        """
        self.print_info("Collect file meta tags..")
        out: Dict[int, list[Dict[str, str]]] = {}

        fm = MowTagFileManipulator()

        for task in track(self.toTransition):
            files = self.getAllTagRelevantFilenamesFor(self.toTreat[task.index])
            try:
                tagdictlist: list[dict[MowTag, str]] = [
                    fm.read_tags(file, tags=tags_all) for file in files
                ]

                out[task.index] = [
                    {
                        key: (
                            value.encode("1252").decode(
                                "utf-8"
                            )  # to avoid problems with umlauten
                            if type(value) is str
                            else value
                        )
                        for key, value in tagdict.items()
                    }
                    for tagdict in tagdictlist
                ]
            except Exception as e:
                out[task.index] = []
                task.skip = True
                task.skipReason = f"Could not parse meta tags: {e}"

        return out

    def prepareTransition(self):
        self.checkFileNamesHaveCorrectTimestamp()

        indexToTags = self.getTagsFromTasks()
        self.checkGrouping(indexToTags)
        self.setMetaTagsToWrite(indexToTags)
        self.deleteBasedOnRating(indexToTags)

    def getTasks(self) -> list[TransitionTask]:
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

    def checkGrouping(self, indexToTags: dict[int, list[dict[MowTag, str]]]):
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
        self, groupnameToTest: str, tagDicts: list[dict[MowTag, str]]
    ):
        for tagDict in tagDicts:
            if MowTag.description not in tagDict:
                continue

            if str(Path(tagDict[MowTag.description])) != str(Path(groupnameToTest)):
                return CheckResult(
                    False,
                    error=f"meta Tag {MowTag.description}:'{str(Path(tagDict[MowTag.description])) if MowTag.description in tagDict else ''}' is not reflecting grouping of '{str(Path(groupnameToTest))}'",
                )

        return CheckResult(ok=True)

    def setMetaTagsToWrite(self, indexToTags: dict[int, list[dict[MowTag, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            tagsDictList = indexToTags[task.index]
            result = self.setMetaTagsToWriteFor(task, tagsDictList)

            if not result.ok:
                task.skip = True
                task.skipReason = result.error

    def setMetaTagsToWriteFor(
        self, task: TransitionTask, tagsDictList: list[dict[MowTag, str]]
    ) -> CheckResult:
        for tag in tags_all:
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
                    tagMissingForExtension.append(
                        splitext(tagsDict[MowTag.sourcefile])[1]
                    )

            if len(allValuesThisTag) == 1 and (
                (
                    atLeastOneMissing
                    or hasattr(self, "jpgSingleSourceOfTruth")
                    and self.jpgSingleSourceOfTruth
                )
            ):
                task.metaTags[tag] = actualTagValue

            elif len(allValuesThisTag) == 0 and tag in tags_expected:
                return CheckResult(
                    False,
                    f"meta tag {tag.name} is missing for extension(s): {','.join(tagMissingForExtension)}",
                )
            elif len(allValuesThisTag) > 1 and tag != MowTag.sourcefile:
                return CheckResult(
                    False,
                    f"meta tag {tag.name} differs between two files that belong to the same medium",
                )

        return CheckResult(ok=True)

    def deleteBasedOnRating(self, indexToTags: dict[int, list[dict[MowTag, str]]]):
        for task in self.toTransition:
            if task.skip:
                continue

            rating = (
                task.metaTags[MowTag.rating]
                if MowTag.rating in task.metaTags
                else int(indexToTags[task.index][0][MowTag.rating])
            )

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
