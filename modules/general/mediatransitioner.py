from dataclasses import dataclass
import os
from os.path import join
from pathlib import Path
from typing import List, Set

from ..general.mediafile import MediaFile
from ..general.verboseprinterclass import VerbosePrinterClass


@dataclass(kw_only=True)
class TansitionerInput:
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for files
    move : if true, moves files, else copies them
    mediatype: Mediafiletype to be used
    verbose: additional output
    dry: don't execute actual transition
    move : move files otherwise copy them
    """

    src: str
    dst: str
    mediatype: MediaFile = None
    recursive = True
    verbose = False
    dry = False


class MediaTransitioner(VerbosePrinterClass):
    """
    Abstract class for transitioning a certain mediafiletype into the next stage.
    """

    def __init__(self, input: TansitionerInput):
        super().__init__(input.verbose)
        self.src = os.path.abspath(input.src)
        self.dst = os.path.abspath(input.dst)
        self.recursive = input.recursive
        self.dry = input.dry
        self.mediatype = input.mediatype

        self.skippedFiles: Set[str] = set()
        self.toTreat: List[MediaFile] = []

        self.treatedfiles = 0

    def __call__(self):
        self.printv(f"Start transition from source {self.src} into {self.dst}")

        self.createDestinationDir()
        self.collectMediaFilesToTreat()

        if not self.dry:
            self.execute()

    def createDestinationDir(self):
        if os.path.isdir(self.dst):
            return
        os.makedirs(self.dst, exist_ok=True)
        self.printv("Created dir", self.dst)

    def collectMediaFilesToTreat(self):
        self.printv("Collect files..")
        for root, _, files in os.walk(self.src):
            if not self.recursive and root != self.src:
                return

            for file in files:
                path = Path(join(root, file))
                mfile = self.mediatype(str(path))
                if not mfile.isValid():
                    continue
                self.toTreat.append(mfile)

        self.printv(f"Collected {len(self.toTreat)} files.")

    def execute(self):
        raise NotImplementedError()
