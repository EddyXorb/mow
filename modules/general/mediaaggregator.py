from typing import List
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput
from .mediagrouper import MediaGrouper
from .filenamehelper import isCorrectTimestamp
from pathlib import Path
from os.path import basename
from exiftool import ExifToolHelper


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

    def prepareTransition(self):
        self.checkFileNamesHaveCorrectTimestamp()
        self.checkGrouping()
        self.checkXMP()

    def getTasks(self) -> List[TransitionTask]:
        self.prepareTransition()
        return self.toTransition

    def checkFileNamesHaveCorrectTimestamp(self):
        for index, file in self.toTreat:
            result = isCorrectTimestamp(str(file)[0:17])
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

    def checkXMP(self):
        with ExifToolHelper() as et:
            for task in self.toTransition:
                if task.skip:
                    continue
                try:
                    tags = et.get_tags(
                        str(self.toTreat[task.index]),
                        tags=[
                            "XMP-date",
                            "XMP-dc:Description",
                            "XMP-dc:Date",
                            "XMP-dc:Source",
                            "XMP:rating",
                        ],
                    )[0]
                    for tag in self.expectedTags:
                        if tag not in tags:
                            task.skip = True
                            task.skipReason = f"Did not find {tag} in XMP-tags"
                            break
                except:
                    task.skip = True
                    task.skipReason = "Could not parse XMP-tags"
