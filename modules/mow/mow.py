from typing import Tuple
import yaml

from os import path
from os.path import join


from ..general.mediatransitioner import TansitionerInput
from ..general.tkinterhelper import getInputDir
from ..general.mediarenamer import RenamerInput
from ..image.imagerenamer import ImageRenamer
from ..image.imageconverter import ImageConverter
from ..video.videoconverter import VideoConverter
from ..video.videorenamer import VideoRenamer
from ..general.mediaconverter import ConverterInput
from ..general.mediagrouper import GrouperInput, MediaGrouper
from ..general.filenamehelper import timestampformat

import logging


class Mow:
    """
    Stands for "M(edia) (fl)OW" - a design to structure your media workflow, be it photos, videos or audio data.
    """

    def __init__(self, settingsfile: str):

        logging.basicConfig(
            format="%(asctime)s [%(levelname)s]: %(message)s",
            level=logging.DEBUG,
            handlers=[logging.FileHandler("mow.log"), logging.StreamHandler()],
            datefmt=timestampformat,
        )

        logging.info(f"{'#'*30} Start new MOW session. {'#'*30}")
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

    def copy(self):
        pass

    def rename(self, useCurrentFilename=False):
        src, dst = self._getSrcDstForStage("rename")

        renamers = [ImageRenamer, VideoRenamer]
        for renamer in renamers:
            self._printEmphasized(f"Apply renamer: {renamer.__name__}")
            renamer(
                RenamerInput(
                    src=src,
                    dst=dst,
                    move=True,
                    verbose=True,
                    writeXMP=True,
                    useCurrentFilename=useCurrentFilename,
                    removeEmptySubfolders=True,
                )
            )()

    def convert(self):
        src, dst = self._getSrcDstForStage("convert")

        converters = [ImageConverter, VideoConverter]
        for converter in converters:
            self._printEmphasized(f"Apply converter: {converter.__name__}")
            converter(
                ConverterInput(
                    src=src,
                    dst=dst,
                    verbose=True,
                    deleteOriginals=False,
                    enforcePassthrough=False,
                    recursive=True,
                    maintainFolderStructure=True,
                    removeEmptySubfolders=True,
                )
            )()

    def group(
        self,
        automate=False,
        distance=12,
        dry=True,
        undoAutomatedGrouping=False,
        addMissingTimestampsToSubfolders=False,
    ):
        src, dst = self._getSrcDstForStage("group")
        self._printEmphasized("Group  files")
        MediaGrouper(
            GrouperInput(
                src=src,
                dst=dst,
                verbose=True,
                recursive=True,
                maintainFolderStructure=True,
                writeXMP=True,
                removeEmptySubfolders=True,
                automaticGrouping=automate,
                separationDistanceInHours=distance,
                dry=dry,
                addMissingTimestampsToSubfolders=addMissingTimestampsToSubfolders,
                undoAutomatedGrouping=undoAutomatedGrouping,
            )
        )()

    def rate(self):
        pass

    def tag(self):
        pass

    def localize(self):
        pass

    def aggregate(self):
        pass

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

    def _getStageFolder(self, stagename: str) -> str:
        return join(self.settings["workingdir"], self.stageToFolder[stagename])

    def _getSrcDstForStage(self, stage: str) -> Tuple[str, str]:
        return self._getStageFolder(stage), self._getStageFolder(
            self._getStageAfter(stage)
        )

    def _printEmphasized(self, toprint: str):
        logging.info(f"{'#'*10} {toprint} {'#'*10}")
