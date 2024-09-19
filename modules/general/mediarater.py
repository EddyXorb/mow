from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, List, Tuple
from os.path import basename, dirname
from pathlib import Path
from tqdm import tqdm

from ..general.checkresult import CheckResult
from ..general.mediafile import MediaFile

from .mediatransitioner import MediaTransitioner, TransitionerInput, TransitionTask
from ..general.medafilefactories import createAnyValidMediaFile

from ..video.videofile import (
    VideoFile,
)  # replace this. The rater should be agnostic to concrete filetype

from exiftool import ExifToolHelper


class MediaRater(MediaTransitioner):
    def __init__(self, input: TransitionerInput, overrulingfiletype: str = None):
        input.mediaFileFactory = createAnyValidMediaFile
        input.writeXMPTags = True
        super().__init__(input)
        self.overrulingfiletype = overrulingfiletype

    def getTasks(self) -> List[TransitionTask]:
        self.printv("Check every file for rating..")

        out: List[TransitionTask] = []

        with ExifToolHelper() as et:
            for index, file in tqdm(enumerate(self.toTreat), total=len(self.toTreat)):
                out.append(self.getTransitionTask(et, index, file))
        return out

    def getTransitionTask(
        self, et: ExifToolHelper, index: int, file: MediaFile
    ) -> TransitionTask:
        try:
            if isinstance(
                file, VideoFile
            ):  # TODO: remove this special case for videos: always rating 2
                return TransitionTask(index, XMPTags={"XMP:Rating": 2})

            filenames = file.getAllFileNames()
            tags = et.get_tags(filenames, "XMP:Rating")
            ratings = {
                file: filetags["XMP:Rating"]
                for file, filetags in zip(filenames, tags)
                if "XMP:Rating" in filetags
            }

            all_ratings = list(set(ratings.values()))
            match len(all_ratings):
                case 0:
                    return TransitionTask.getFailed(index, "No rating found!")
                case 1:
                    if len(tags) > 1:
                        return TransitionTask(
                            index, XMPTags={"XMP:Rating": all_ratings[0]}
                        )
                    return TransitionTask(index)
                case _:
                    if self.overrulingfiletype is not None:
                        overruled_ratings = {
                            key: value
                            for key, value in ratings.items()
                            if key.endswith(self.overrulingfiletype)
                        }
                        if len(set(overruled_ratings.values())) == 1:
                            self.printv(
                                f"Overruling file type set to {self.overrulingfiletype}, which causes rating {list(overruled_ratings.values())[0]} for files {list(overruled_ratings.keys())}"
                            )
                            return TransitionTask(
                                index,
                                XMPTags={
                                    "XMP:Rating": list(overruled_ratings.values())[0]
                                },
                            )
                        else:
                            self.printv(
                                f"Overruling file type set, but different ratings found: {overruled_ratings}"
                            )
                    return TransitionTask.getFailed(
                        index, f"Different ratings found:{ratings}"
                    )
        except Exception as e:
            return TransitionTask.getFailed(
                index, f"Problem during reading rating from XMP: {e}"
            )
