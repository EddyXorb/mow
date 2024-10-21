import os
from typing import DefaultDict, List
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
        excludesearchfolders: List[str],
    ):
        super().__init__(verbose=True)
        self.missingdir = sourcedir
        self.searchdir = searchdir
        self.excludesarchdirs = map(lambda x: os.path.abspath(x), excludesearchfolders)
        self.filessearched: DefaultDict[str, List[ImageFile]] = self.createFolderDict(
            self.searchdir, self.excludesarchdirs
        )
        self.filessuspectedtomiss: DefaultDict[str, List[ImageFile]] = (
            self.createFolderDict(self.missingdir)
        )
        self.missingfiles: List[ImageFile] = []

    def createFolderDict(
        self, dir: str, excludedirs: List[str] = []
    ) -> DefaultDict[ImageFile, List[ImageFile]]:
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
            if not name in self.filessearched:
                alternativeName = ImageRenamer.getNewImageFileNameFor(
                    imagefiles[0].getJpg()
                )
                if alternativeName is None or not alternativeName in self.filessearched:
                    self.missingfiles.append(imagefiles[0])

        self.print_info(
            f"Finished image search and found {len(self.missingfiles)} missing files."
        )
        self.print_info(f"Missing files are:")
        for file in self.missingfiles:
            self.print_info(file.getJpg())
