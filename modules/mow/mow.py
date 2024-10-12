import datetime
import os
from pathlib import Path
import sys
from typing import Callable, Dict, Tuple
import yaml

from os import path
from os.path import join
import logging

from ..image.imagefile import ImageFile
from ..video.videofile import VideoFile
from ..general.mediaconverter import PassthroughConverter
from ..general.mediacopier import MediaCopier
from ..general.mediatransitioner import TransitionerInput
from ..general.tkinterhelper import getInputDir, getInputFile
from ..general.mediarenamer import RenamerInput
from ..image.imagerenamer import ImageRenamer
from ..image.imageconverter import ImageConverter
from ..video.videoconverter import VideoConverter
from ..video.videorenamer import VideoRenamer
from ..audio.audiorenamer import AudioRenamer
from ..general.mediagrouper import GrouperInput, MediaGrouper
from ..general.filenamehelper import timestampformat
from ..general.mediarater import MediaRater
from ..image.imageaggregator import ImageAggregator
from ..video.videoaggregator import VideoAggregator
from ..general.medialocalizer import (
    BaseLocalizerInput,
    LocalizerInput,
    MediaLocalizer,
)
from ..general.mediatagger import MediaTagger
from ..general.mediaaggregator import AggregatorInput

from .mowstatusprinter import MowStatusPrinter


class Mow:
    """
    Stands for "M(edia) (fl)OW" - a design to structure your media workflow, be it photos, videos or audio data.
    """

    def __init__(self, settingsfile: str, dry: bool = True, filter: str = None):
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s]: %(message)s",
            level=logging.INFO,
            handlers=[
                logging.FileHandler("mow.log", "a", "utf-8"),
                logging.StreamHandler(),
            ],
            datefmt=timestampformat,
        )
        # logging.info(f"{'#'*30} Start new MOW session. {'#'*30}")

        self.settingsfile = settingsfile
        self.settings = (
            self._readsettings()
        )  # settings are stored in yaml-file at root dir of the script and tags are snake_case
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
        self.basicInputParameter = {
            "verbose": True,
            "recursive": True,
            "maintainFolderStructure": True,
            "removeEmptySubfolders": True,
            "writeMetaTags": True,
            "move": True,
            "dry": dry,
            "filter": filter,
            "settings": self.settings,
        }

    def copy(self, askForNewSource: bool = False):
        self._read_settings_folder_path_if_missing(
            key="copy_source_dir",
            message="Specify source dir from where to copy!",
            force=askForNewSource,
        )

        src, dst = self._getSrcDstForStage("copy")
        self._printEmphasized(f"Stage copy")

        MediaCopier(TransitionerInput(src=src, dst=dst, **self.basicInputParameter))()

    def rename(self, useCurrentFilename=False, replace=""):
        src, dst = self._getSrcDstForStage("rename")
        renamers = [ImageRenamer, VideoRenamer, AudioRenamer]
        for renamer in renamers:
            self._printEmphasized(f"Stage rename: {renamer.__name__}")
            renamer(
                RenamerInput(
                    src=src,
                    dst=dst,
                    useCurrentFilename=useCurrentFilename,
                    replace=replace,
                    **self.basicInputParameter,
                )
            )()

    def convert(self, enforcePassthrough: bool = False):
        src, dst = self._getSrcDstForStage("convert")
        converters = (
            [ImageConverter, VideoConverter]
            if not enforcePassthrough
            else [PassthroughConverter]
        )
        for converter in converters:
            self._printEmphasized(f"Stage Convert: {converter.__name__}")
            if converter == PassthroughConverter:
                converter(
                    TransitionerInput(
                        src=src,
                        dst=dst,
                        **self.basicInputParameter,
                    ),
                    valid_extensions=ImageFile.supportedJpgFormats
                    + ImageFile.supportedRawFormats
                    + VideoFile.supportedFormats,
                )()
            else:
                self._read_settings_file_path_if_missing(
                    "dng_converter_exe",
                    "Specify path to dng converter executable!",
                )
                converter(
                    TransitionerInput(
                        src=src,
                        dst=dst,
                        **self.basicInputParameter,
                    )
                )()

    def group(
        self,
        automate=False,
        distance=12,
        undoAutomatedGrouping=False,
        addMissingTimestampsToSubfolders=False,
        checkSequence=False,
    ):
        src, dst = self._getSrcDstForStage("group")
        self._printEmphasized("Stage Group")
        MediaGrouper(
            GrouperInput(
                src=src,
                dst=dst,
                automaticGrouping=automate,
                separationDistanceInHours=distance,
                addMissingTimestampsToSubfolders=addMissingTimestampsToSubfolders,
                undoAutomatedGrouping=undoAutomatedGrouping,
                checkSequence=checkSequence,
                **self.basicInputParameter,
            )
        )()

    def rate(self, overrulingfiletype: str = None):
        src, dst = self._getSrcDstForStage("rate")
        self._printEmphasized("Stage Rate")
        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                **self.basicInputParameter,
            ),
            overrulingfiletype=overrulingfiletype,
        )()

    def tag(self):
        src, dst = self._getSrcDstForStage("tag")
        self._printEmphasized("Stage Tag")
        MediaTagger(
            TransitionerInput(
                src=src,
                dst=dst,
                **self.basicInputParameter,
            )
        )()

    def localize(self, localizerInput: BaseLocalizerInput):
        src, dst = self._getSrcDstForStage("localize")
        self._printEmphasized("Stage Localize")
        MediaLocalizer(
            LocalizerInput(
                localizerInput,
                TransitionerInput(src=src, dst=dst, **self.basicInputParameter),
            )
        )()

    def aggregate(self, jpgIsSingleSourceOfTruth: bool):
        src, dst = self._getSrcDstForStage("aggregate")
        self._printEmphasized("Stage Aggregate")
        for aggregator in [ImageAggregator, VideoAggregator]:
            aggregator(
                AggregatorInput(
                    src=src,
                    dst=dst,
                    jpgSingleSourceOfTruth=jpgIsSingleSourceOfTruth,
                    **self.basicInputParameter,
                )
            )()

    def status(self):
        MowStatusPrinter(
            self.stages, self.stageToFolder, self.settings["working_dir"]
        ).printStatus()

    def list_todos(self, stage: str):
        items = os.listdir(
            Path(self.settings["working_dir"]) / self.stageToFolder[stage]
            if stage != "copy"
            else self.settings["copy_source_dir"]
        )
        print(
            "\n".join(items if len(items) < 100 else items[:100]),
            flush=True,
        )

        if len(items) > 100:
            print(f"... and {len(items) - 100} more items ...")

    def _getStageAfter(self, stage: str) -> str:
        if stage not in self.stageToFolder:
            raise Exception(f"Could not find stage {stage}")
        indexStage = self.stages.index(stage)
        if indexStage + 1 > len(self.stages) - 1:
            raise Exception(f"Cannot get stage after {stage}!")
        return self.stages[indexStage + 1]

    def _readsettings(self) -> Dict[str, str]:
        out = {}
        if not path.exists(self.settingsfile):
            out["working_dir"] = getInputDir("Specify working directory!")
        else:
            with open(self.settingsfile, "r") as f:
                out = yaml.safe_load(f)
            if out is None:
                out = {}
            if not "working_dir" in out:
                out["working_dir"] = getInputDir("Specify working directory!")

        with open(self.settingsfile, "w") as f:
            yaml.safe_dump(out, f)

        return out

    def _getStageFolder(self, stagename: str) -> str:
        if (
            stagename == "copy"
        ):  # this is the only exception: for copying from foreign sources
            return self.settings["copy_source_dir"]

        return join(self.settings["working_dir"], self.stageToFolder[stagename])

    def _getSrcDstForStage(self, stage: str) -> Tuple[str, str]:
        return self._getStageFolder(stage), self._getStageFolder(
            self._getStageAfter(stage)
        )

    def _printEmphasized(self, toprint: str):
        logging.info(f"{'#'*10} {toprint} {'#'*10}")

    def _read_settings_folder_path_if_missing(
        self, key: str, message: str, force=False
    ):
        self._read_settings_entity_if_missing(key, message, force, getInputDir)

    def _read_settings_file_path_if_missing(self, key: str, message: str, force=False):
        self._read_settings_entity_if_missing(key, message, force, getInputFile)

    def _read_settings_entity_if_missing(
        self, key: str, message: str, force, reader: Callable[[str], str]
    ):
        if not force and key in self.settings:
            return

        entity = reader(message)
        if entity is None:
            print(f"Could not read {key}! Abort.")
            sys.exit()
        self.settings[key] = entity

        with open(self.settingsfile, "w") as f:
            yaml.safe_dump(self.settings, f)
