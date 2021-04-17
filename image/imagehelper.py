import os
import datetime as dt

from PIL import Image, ExifTags


def getExifDateFrom(file: str) -> dt.datetime:
    img = Image.open(file)
    img_exif = img.getexif()

    if img_exif is None:
        raise Exception("Sorry, image has no exif data: ", file)
    else:
        date = img_exif[306]
        return dt.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
