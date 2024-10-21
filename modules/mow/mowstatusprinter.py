import os
from os.path import join
from typing import Dict, List
from math import sqrt

from ..general.verboseprinterclass import VerbosePrinterClass
from ..general.mediatransitioner import DELETE_FOLDER_NAME
from ..general.medafilefactories import createAnyValidMediaFile


class MowStatusPrinter(VerbosePrinterClass):

    def __init__(
        self, stages: list[str], stageToFolder: Dict[str, str], workingdir: str
    ):
        """
        stages: stagename, stagefolder-path
        """
        super().__init__(verbose=True)
        self.stages = stages
        self.stageToFolder = stageToFolder
        self.workingdir = workingdir

    def printStatus(self):
        allfiles = self.collectAllMediafiles()

        nrallfiles = sum([len(files) for files in allfiles.values()])
        weightedSum = 0

        for cnt, stage in enumerate(self.stages):
            files = allfiles[stage]
            if len(files) > 0:
                self.print_info(
                    f"{stage}: {len(files)} mediafiles ({(100.0 * len(files))/nrallfiles:.0f}%) {'.'*int(sqrt(len(files)))}"
                )

            weightedSum += cnt * len(files)
        self.print_info(f"Number of all files: {nrallfiles}")
        self.print_info(
            f"Overall progress: {float(100*weightedSum)/(len(self.stages)*nrallfiles):.0f} %"
        )

    def collectAllMediafiles(self) -> Dict[str, list[str]]:
        """
        Return: stage to list of all mediafiles found in this stage
        """
        out: Dict[str, list[str]] = {}

        for stage in self.stages:
            out[stage] = []
            for root, dirs, files in os.walk(
                join(self.workingdir, self.stageToFolder[stage])
            ):
                # ignore all files in deleteFolder
                dirs[:] = [d for d in dirs if d != DELETE_FOLDER_NAME]
                for file in files:
                    mediafile = createAnyValidMediaFile(
                        join(root, file), fast_creation=True
                    )
                    if mediafile.isValid():
                        out[stage].append(mediafile)

        return out
