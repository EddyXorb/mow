import os
from typing import DefaultDict
from collections import defaultdict

from ..general.verboseprinterclass import VerbosePrinterClass
from .imagefile import ImageFile
from .imagerenamer import ImageRenamer


class ImageSearcher(VerbosePrinterClass):
    """
    Searches for suspected missing files. E.g. if you have an SD-Card and are not sure if you already have saved the images on it, this tool will find the missing ones.
    """

    def __init__(
        self,
        sourcedir: str,
        searchdir: str,
        excludesearchfolders: list[str],
    ):
        super().__init__(verbose=True)
        self.missingdir = sourcedir
        self.searchdir = searchdir
        self.excludesarchdirs = map(lambda x: os.path.abspath(x), excludesearchfolders)
        self.filessearched: DefaultDict[str, list[ImageFile]] = self.createFolderDict(
            self.searchdir, self.excludesarchdirs
        )
        self.filessuspectedtomiss: DefaultDict[str, list[ImageFile]] = (
            self.createFolderDict(self.missingdir)
        )
        self.missingfiles: list[ImageFile] = []

    def createFolderDict(
        self, dir: str, excludedirs: list[str] = []
    ) -> DefaultDict[ImageFile, list[ImageFile]]:
        out = defaultdict(list)

        for root, dirs, files in os.walk(dir, topdown=True):
            for dir in excludedirs:
                if dir in dirs:
                    dirs.remove(dir)
                    self.print_info(f"Excluded {dir} from search in searchdir.")

            for file in files:
                fullname = os.path.join(root, file)
                imageFile = ImageFile(fullname)
                if imageFile.isValid():
                    out[file].append(imageFile)

        self.print_info(f"Created dict with {len(out)} entries.")

        return out

    def findMissingFiles(self):
        for name, imagefiles in self.filessuspectedtomiss.items():
            if name not in self.filessearched:
                alternativeName = ImageRenamer.getNewImageFileNameFor(
                    imagefiles[0].getJpg()
                )
                if alternativeName is None or alternativeName not in self.filessearched:
                    self.missingfiles.append(imagefiles[0])

        self.print_info(
            f"Finished image search and found {len(self.missingfiles)} missing files."
        )
        self.print_info("Missing files are:")
        for file in self.missingfiles:
            self.print_info(file.getJpg())
