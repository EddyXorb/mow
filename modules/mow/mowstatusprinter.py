from collections import defaultdict
import os
from os.path import join
from typing import Dict, List, DefaultDict
from math import sqrt
from ..general.medafilefactories import createAnyValidMediaFile


class MowStatusPrinter:
    def __init__(
        self, stages: List[str], stageToFolder: Dict[str, str], workingdir: str
    ):
        """
        stages: stagename, stagefolder-path
        """
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
                print(f"{stage}: {len(files)} mediafiles ({(100.0 * len(files))/nrallfiles:.0f}%) {'.'*int(sqrt(len(files)))}")
                
            weightedSum += cnt * len(files)
        print(f"\nNumber of all files: {nrallfiles}")
        print(
            f"Overall progress: {float(100*weightedSum)/(len(self.stages)*nrallfiles):.0f} %"
        )

    def collectAllMediafiles(self) -> Dict[str, List[str]]:
        """
        Return: stage to list of all mediafiles found in this stage
        """
        out: Dict[str, List[str]] = {}

        for stage in self.stages:
            out[stage] = []
            for root, dirs, files in os.walk(
                join(self.workingdir, self.stageToFolder[stage])
            ):
                # ignore all files in deleteFolder
                dirs[:] = [d for d in dirs if d != "_deleted"]
                for file in files:
                    mediafile = createAnyValidMediaFile(join(root, file))
                    if mediafile.isValid():
                        out[stage].append(mediafile)

        return out
