import os
import datetime as dt

from PIL import Image, ExifTags
from exiftool import ExifToolHelper
import pathlib


def getFileCreationDateFrom(file: str) -> dt.datetime:
    fname = pathlib.Path(file)
    return dt.datetime.fromtimestamp(fname.stat().st_ctime, tz=dt.timezone.utc)


def getMediaCreationDateFrom(file: str, verbose=False) -> dt.datetime:
    try:
        date = None
        img = Image.open(file)
        img_exif = img.getexif()
        exifvalueOriginalCreation = 36867
        exifvalueChangedDate = 306
        if img_exif is None or (
            exifvalueOriginalCreation not in img_exif
            and exifvalueChangedDate not in img_exif
        ):
            date = getFileCreationDateFrom(file)
            if verbose:
                print(
                    f"Had to use file creation date {date} for file {file} due to missing metadata."
                )
            return date
        else:
            if exifvalueOriginalCreation in img_exif:
                date = img_exif[exifvalueOriginalCreation]
            else:
                date = img_exif[exifvalueChangedDate]

        return dt.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")

    except:
        return getFileCreationDateFrom(file)


def getDateTimeFileNameFor(file: str) -> str:
    date = getMediaCreationDateFrom(file)
    prefixDate = f"{date:%Y-%m-%d@%H%M%S}"
    return os.path.join(
        os.path.dirname(file), prefixDate + "_" + os.path.basename(file)
    )
