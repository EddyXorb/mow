import os
import datetime as dt

from PIL import Image, ExifTags


def getExifDateFrom(file: str) -> dt.datetime:
    img = Image.open(file)
    img_exif = img.getexif()
    exifvalueOriginalCreation = 36867 
    exifvalueChangedDate = 306
    if img_exif is None:
        raise Exception("Sorry, image has no exif data: ", file)
    elif exifvalueOriginalCreation not in img_exif and exifvalueChangedDate not in img_exif:
        raise Exception(f"Sorry, image has exif data but it's creation date value is not present")
    else:
        if exifvalueOriginalCreation in img_exif:
            date = img_exif[exifvalueOriginalCreation]
        else:
            date = img_exif[exifvalueChangedDate]
        return dt.datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
