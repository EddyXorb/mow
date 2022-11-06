#%%

import os
import datetime as dt
import numpy as np
from typing import List
from collections import defaultdict

from ..general.filenamehelper import getMediaCreationDateFrom
from .imagefile import ImageFile
from general.verboseprinterclass import VerbosePrinterClass


class DateImageFile(ImageFile):
    def __init__(self, file):
        super().__init__(file)
        if self.isValid():
            self.date: dt.datetime = getMediaCreationDateFrom(self.getJpg())
            self.baseTime: dt.datetime = None


class ImageClusterer(VerbosePrinterClass):
    """
    src : full path to folder containing images
    hoursmaxdiff : cluster
    move : if true, files are moved instead of copied
    test : don't copy/move anything, print only files that would be copied.
    """

    def __init__(
        self,
        src: str,
        dst: str = None,
        hoursmaxdiff: int = 24,
        move: bool = False,
        verbose=False,
        test: bool = False,
    ):
        if not os.path.isdir(src):
            print(src)
            raise Exception("Given src is not a dir!")
        if hoursmaxdiff < 1:
            raise Exception("Hoursmaxdiff is smaller than 1!")

        self.src = os.path.abspath(src)
        self.dst = dst if dst is not None else os.path.join(self.src, "clustered")
        self.secondsmaxdiff = 3600 * hoursmaxdiff
        self.move = move
        self.verbose = verbose
        self.test = test

        self.folderformatstring = "%Y-%m-%dH%H" if hoursmaxdiff < 24 else "%Y-%m-%d"
        self.files: List[DateImageFile] = []
        self.nrcluster = 1
        self.clusterToSize = defaultdict(lambda: int(0))

        self.collectDateImages()

        if len(self.files) == 0:
            print("No files in folder", self.src, ". Do nothing.")
            return

        self.fillBaseTimes()
        self.sortFiles()
        self.clusterFiles()
        self.printSummary()

    def printSummary(self):
        print(
            "Would treat" if self.test else "Treated",
            len(self.files),
            "images in",
            self.nrcluster,
            "clusters.",
        )

        for cluster, files in self.clusterToSize.items():
            self.printv("Cluster", cluster, "contains", files, "files.")

    def collectDateImages(self) -> List[DateImageFile]:
        files = os.listdir(self.src)
        for file in files:
            ifile = DateImageFile(os.path.join(self.src, file))
            if not ifile.isValid():
                continue

            self.files.append(ifile)

    def sortFiles(self):
        self.files.sort(key=lambda x: x.date)

    def getClusterNameFrom(self, time: dt.datetime) -> str:
        return time.strftime(self.folderformatstring)

    def fillBaseTimes(self):
        lastTime = self.files[0].date
        lastBaseTime = self.files[0].date
        self.printv("New cluster", self.getClusterNameFrom(lastBaseTime))

        for im in self.files:
            sec = (im.date - lastTime).total_seconds()
            if sec > self.secondsmaxdiff:
                lastBaseTime = im.date
                self.nrcluster += 1
                self.printv("New cluster", self.getClusterNameFrom(lastBaseTime))

            self.clusterToSize[self.getClusterNameFrom(lastBaseTime)] += 1
            lastTime = im.date
            im.baseTime = lastBaseTime

    def clusterFiles(self):
        for im in self.files:
            folder = im.baseTime.strftime(self.folderformatstring)

            newFolder = os.path.join(self.dst, folder)
            dst = os.path.join(newFolder, os.path.basename(im.getJpg()))

            self.printv("Would create" if self.test else "Create", "image in", dst)
            if self.test:
                continue

            if self.move:
                im = im.moveTo(dst)
            else:
                im.copyTo(dst)
