import yaml
from ..general.tkinterhelper import getInputDir
from os import path
from os.path import join
import os
from ..image.imagerenamer import ImageRenamer
from ..video.videorenamer import VideoRenamer
from exiftool import ExifToolHelper


def remove_empty_subfolders_of(path_to_remove):
    to_remove = os.path.abspath(path_to_remove)
    for path, _, _ in os.walk(to_remove, topdown=False):
        if path == to_remove:
            continue
        if len(os.listdir(path)) == 0:
            os.rmdir(path)


class Mow:
    """
    Stands for "M(edia) (fl)OW" - a design to structure your media workflow, be it photos, videos or audio data.
    """

    def __init__(self, settingsfile: str):
        self.settingsfile = settingsfile
        self.settings = self._readsettings()
        self.stageFolders = [
            "1_copy",
            "2_rename",
            "3_convert",
            "4_group",
            "5.1_rate",
            "5.2_tag",
            "5.3_localize",
            "6_aggregate",
            "7_archive",
        ]
        self.stages = [folder.split("_")[1] for folder in self.stageFolders]
        self.stageToFolder = {
            folder.split("_")[1]: folder for folder in self.stageFolders
        }

    def _getStageAfter(self, stage: str) -> str:
        if stage not in self.stageToFolder:
            raise Exception(f"Could not find stage {stage}")
        indexStage = self.stages.index(stage)
        if indexStage + 1 > len(self.stages) - 1:
            raise Exception(f"Cannot get stage after {stage}!")
        return self.stages[indexStage + 1]

    def _readsettings(self) -> str:
        if not path.exists(self.settingsfile):
            workingdir = getInputDir("Specify working directory!")
            with open(self.settingsfile, "w") as f:
                yaml.safe_dump({"workingdir": workingdir}, f)

        with open(self.settingsfile, "r") as f:
            return yaml.safe_load(f)

    def copy(self):
        pass

    def rename(self):
        src = join(self.settings["workingdir"], self.stageToFolder["rename"])
        dst = join(
            self.settings["workingdir"],
            self.stageToFolder[self._getStageAfter("rename")],
        )
        
        renamers = [ImageRenamer, VideoRenamer]
        for renamer in renamers:
            renamer(
                src,
                dst,
                move=True,
                verbose=True,
                writeXMP=True,
            )()

        remove_empty_subfolders_of(src)

    def group(self):
        pass

    def rate(self):
        pass

    def tag(self):
        pass

    def localize(self):
        pass

    def aggregate(self):
        pass
