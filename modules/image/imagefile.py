from __future__ import annotations
import os
import os
from shutil import copyfile, move
from typing import List, Callable

from ..general.mediafile import MediaFile
import datetime as dt

from PIL import Image


class ImageFile(MediaFile):
    supportedjpgFormats = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    supportedRawFormats = [".ORF", ".NEF"]

    def __init__(self, file):
        """
        file must be path to a jpg-file!
        """
        super().__init__(path=file, validExtensions=self.supportedjpgFormats)
        if not self.isValid():
            return

        for rawExt in ImageFile.supportedRawFormats:
            rawFileCandidate = os.path.splitext(file)[0] + rawExt
            if os.path.exists(rawFileCandidate):
                self.extensions.append(rawExt)
                self.nrFiles += 1

    def getJpg(self) -> str:
        return self.pathnoext + self.extensions[0]

    def getRaw(self) -> str:
        if len(self.extensions) > 1:
            return self.pathnoext + self.extensions[1]
        return None

    def readDateTime(self):
        try:
            date = None
            img = Image.open(self.getJpg())
            img_exif = img.getexif()
            exifvalueOriginalCreation = 36867
            exifvalueChangedDate = 306
            if img_exif is None or (
                exifvalueOriginalCreation not in img_exif
                and exifvalueChangedDate not in img_exif
            ):
                return None
            else:
                if exifvalueOriginalCreation in img_exif:
                    date = img_exif[exifvalueOriginalCreation]
                else:
                    date = img_exif[exifvalueChangedDate]

            return dt.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
        except:
            return None
