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

from exiftool import ExifToolHelper


class MediaRater(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = createAnyValidMediaFile
        input.writeXMPTags = True
        super().__init__(input)

    def getTasks(self) -> List[TransitionTask]:
        self.printv("Check every file for rating..")

        out: List[TransitionTask] = []

        with ExifToolHelper() as et:
            for index, file in tqdm(enumerate(self.toTreat), total=len(self.toTreat)):
                out.append(self.getTransitionTask(et, index, file))
        return out

    def getTransitionTask(
        self, et: ExifToolHelper, index: int, file: MediaFile
    ) -> Tuple[CheckResult, int]:
        try:
            tags = et.get_tags(file.getAllFileNames(), "XMP:Rating")
            ratings = [
                filetags["XMP:Rating"] for filetags in tags if "XMP:Rating" in filetags
            ]
            match len(set(ratings)):
                case 0:
                    return TransitionTask.getFailed(index, "No rating found!")
                case 1:
                    if len(tags) > 1:
                        return TransitionTask(index, XMPTags={"XMP:Rating": ratings[0]})
                    return TransitionTask(index)
                case _:
                    return TransitionTask.getFailed(index, f"Different ratings found:{ratings}")
        except Exception as e:
            return TransitionTask.getFailed(
                index, f"Problem during reading rating from XMP: {e}"
            )
