from __future__ import annotations
import os
import os
from shutil import copyfile, move
from typing import List, Callable

from ..general.mediafile import MediaFile
import datetime as dt

from PIL import Image


class ImageFile(MediaFile):
    supportedJpgFormats = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    supportedRawFormats = [".ORF", ".NEF", ".dng", ".DNG"]

    def __init__(self, file):
        super().__init__(
            path=file,
            validExtensions=self.supportedJpgFormats + self.supportedRawFormats,
        )
        if not self.isValid():
            return

        for ext in ImageFile.supportedRawFormats + ImageFile.supportedJpgFormats:
            if ext in self.extensions:
                continue

            otherFileCandidate = os.path.basename(self.pathnoext) + ext
            if otherFileCandidate in os.listdir(
                os.path.dirname(self.pathnoext)
            ):  # this is to avoid problems regarding case-insensitivity on windows. Otherwise .JPG and .jpg will both be in the list
                self.extensions.append(ext)

    def getJpg(self) -> str:
        jpg_ending = set(self.supportedJpgFormats).intersection(set(self.extensions))
        if len(jpg_ending) == 0:
            return None
        return self.pathnoext + jpg_ending.pop()

    def getRaw(self) -> str:
        raw_ending = set(self.supportedRawFormats).intersection(set(self.extensions))
        if len(raw_ending) == 0:
            return None
        return self.pathnoext + raw_ending.pop()

    def markRawAsRemoved(self):
        if len(self.extensions) > 1:
            self.extensions.pop()

    def readDateTime(self):
        try:
            date = None
            img = Image.open(self.getJpg())
            img_exif = img._getexif()
            exifvalueOriginalCreation = 36867
            exifValueDigitized = 36868
            exifvalueChangedDate = 306
            if img_exif is None or (
                exifvalueOriginalCreation not in img_exif
                and exifValueDigitized not in img_exif
                and exifvalueChangedDate not in img_exif
            ):
                return None
            else:
                if exifvalueOriginalCreation in img_exif:
                    date = img_exif[exifvalueOriginalCreation]
                elif exifValueDigitized in img_exif:
                    date = img_exif[exifValueDigitized]
                else:
                    date = img_exif[exifvalueChangedDate]

            return dt.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
        except:
            return None
