import os
import datetime as dt
from os.path import basename
import pathlib

from ..general.mediafile import MediaFile
from ..general.checkresult import CheckResult
from ..image.imagefile import ImageFile
from ..video.videofile import VideoFile

import logging

timestampformat = "%Y-%m-%d@%H%M%S"


def getFileModifyDateFrom(file: str) -> dt.datetime:
    fname = pathlib.Path(file)
    return dt.datetime.fromtimestamp(fname.stat().st_mtime, tz=dt.timezone.utc)


def getMediaCreationDateFrom(file: str) -> dt.datetime:
    result = None
    toCheck = [ImageFile, VideoFile]
    for mediatype in toCheck:
        mediafile: MediaFile = mediatype(file)
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


def isCorrectTimestamp(candidate: str) -> CheckResult:
    if candidate[10] != "@":
        return CheckResult(
            False,
            f"Candidate {candidate} does not have '@' at index 10, but {candidate[10]}",
        )

    try:
        dummy = dt.datetime.strptime(candidate[0:17], timestampformat)
        return CheckResult(
            dummy is not None, "Could not parse timestamp, invalid format"
        )
    except:
        return CheckResult(False, f"Candidate {candidate}'s timestamp is wrong")


def extractDatetimeFrom(file: str, verbose=True) -> dt.datetime:
    try:
        return dt.datetime.strptime(basename(file)[0:17], timestampformat)
    except Exception as e:
        if verbose:
            logging.warning(
                f"Could not get time from timestamp of file {file} because of {e}"
            )
        return None
