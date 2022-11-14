import os
import datetime as dt

import pathlib

from ..image.imagefile import ImageFile
from ..video.videofile import VideoFile

timestampformat = "%Y-%m-%d@%H%M%S"


def getFileModifyDateFrom(file: str) -> dt.datetime:
    fname = pathlib.Path(file)
    return dt.datetime.fromtimestamp(fname.stat().st_mtime, tz=dt.timezone.utc)


def getMediaCreationDateFrom(file: str, verbose=False) -> dt.datetime:
    result = None
    toCheck = [ImageFile, VideoFile]
    for mediatype in toCheck:
        mediafile = mediatype(file)
        if not mediafile.isValid():
            continue
        result = mediafile.readDateTime()
        if result is not None:
            return result

    if result is None:
        result = getFileModifyDateFrom(file)

    return result


def getDateTimeFileNameFor(file: str) -> str:
    date = getMediaCreationDateFrom(file)
    prefixDate = date.strftime(timestampformat)
    return os.path.join(
        os.path.dirname(file), prefixDate + "_" + os.path.basename(file)
    )
