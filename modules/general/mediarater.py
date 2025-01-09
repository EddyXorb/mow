from pathlib import Path
from rich.progress import track
import os

from modules.mow.mowtags import MowTag

from ..general.mediafile import MediaFile

from .mediatransitioner import MediaTransitioner, TransitionerInput, TransitionTask
from ..general.medafilefactories import createAnyValidMediaFile

from ..video.videofile import (
    VideoFile,
)  # replace this. The rater should be agnostic to concrete filetype

from exiftool import ExifToolHelper
import traceback


class MediaRater(MediaTransitioner):
    def __init__(
        self,
        input: TransitionerInput,
        overrulingfiletype: str = None,
        enforced_rating: int = None,
    ):
        input.mediaFileFactory = createAnyValidMediaFile
        input.writeMetaTags = True
        super().__init__(input)
        self.overrulingfiletype = overrulingfiletype
        self.enforced_rating = enforced_rating

    def getTasks(self) -> list[TransitionTask]:
        self.print_info("Check every file for rating..")

        out: list[TransitionTask] = []

        with ExifToolHelper() as et:
            for index, file in track(enumerate(self.toTreat), total=len(self.toTreat)):
                out.append(self.getTransitionTask(et, index, file))
        return out

    def getTransitionTask(
        self, et: ExifToolHelper, index: int, file: MediaFile
    ) -> TransitionTask:
        try:
            if self.enforced_rating and self.enforced_rating in range(1, 6):
                return TransitionTask(
                    index, metaTags={MowTag.rating: self.enforced_rating}
                )

            if isinstance(
                file, VideoFile
            ):  # TODO: remove this special case for videos: always rating 2
                return TransitionTask(index, metaTags={MowTag.rating: 2})

            filenames = file.getAllFileNames()
            tags = [self.fm.read_tags(file, tags=[MowTag.rating]) for file in filenames]
            ratings = {
                file: filetags[MowTag.rating]
                for file, filetags in zip(filenames, tags)
                if MowTag.rating in filetags
            }

            all_ratings = list(set(ratings.values()))
            match len(all_ratings):
                case 0:
                    return TransitionTask.getFailed(index, "No rating found!")
                case 1:
                    if len(tags) > 1:
                        return TransitionTask(
                            index, metaTags={MowTag.rating: all_ratings[0]}
                        )
                    return TransitionTask(index)
                case _:
                    if self.overrulingfiletype is not None:
                        overruled_ratings = {
                            os.path.basename(key): value
                            for key, value in ratings.items()
                            if key.suffix.replace(".","") == self.overrulingfiletype
                        }
                        if len(set(overruled_ratings.values())) == 1:
                            self.print_info(
                                f"Overruling file type set to {self.overrulingfiletype}, which causes rating {list(overruled_ratings.values())[0]} for files {list(overruled_ratings.keys())}"
                            )
                            return TransitionTask(
                                index,
                                metaTags={
                                    MowTag.rating: list(overruled_ratings.values())[0]
                                },
                            )
                        else:
                            self.print_info(
                                f"Overruling file type set, but different ratings found: {overruled_ratings}"
                            )

                    output_ratings = {
                        os.path.basename(file): rating
                        for (file, rating) in ratings.items()
                    }
                    return TransitionTask.getFailed(
                        index, f"Different ratings found: {output_ratings}"
                    )
        except Exception as e:
            stacktrace = traceback.format_exc()
            return TransitionTask.getFailed(
                index,
                f"Problem during reading rating from meta tags: {e}, stacktrace: {stacktrace}",
            )
