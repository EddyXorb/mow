from __future__ import annotations
import os
from pathlib import Path

from ..general.mediafile import MediaFile
import datetime as dt

from PIL import Image


class ImageFile(MediaFile):
    supportedJpgFormats = set({".jpg", ".JPG", ".jpeg", ".JPEG"})
    supportedRawFormats = set({".ORF", ".NEF", ".dng", ".DNG"})
    allSupportedFormats = set(supportedJpgFormats.union(supportedRawFormats))

    def __init__(self, file, check_for_other_extensions=True):
        super().__init__(
            path=file,
            validExtensions=self.allSupportedFormats,
        )
        if not self.isValid() or not check_for_other_extensions:
            return

        path_no_ext = Path(self.pathnoext)
        candidates = [
            item
            for item in path_no_ext.parent.iterdir()
            if item.stem == path_no_ext.name and item.suffix in self.allSupportedFormats
        ]

        for candidate in candidates:
            candidate_new_extension = Path(candidate).suffix
            if candidate_new_extension not in self.extensions:
                self.extensions.append(candidate_new_extension)

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
