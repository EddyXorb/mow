from exiftool import ExifToolHelper
from ..general.mediafile import MediaFile
import datetime as dt


class AudioFile(MediaFile):
    supportedAudioFileEndings = [".MP3", ".mp3", ".wav", ".WAV"]

    def __init__(self, path: str):
        super().__init__(path, validExtensions=self.supportedAudioFileEndings)

    def readDateTime(self) -> dt.datetime:
        file = self.pathnoext + self.extensions[0]
        with ExifToolHelper() as et:
            result = et.get_tags(
                file,
                [
                    "QuickTime:MediaCreateDate",
                    "QuickTime:CreateDate",
                    "File:FileModifyDate",
                ],
            )[0]
            for key, value in result.items():
                if key == "SourceFile":
                    continue
                return dt.datetime.strptime(value[0:19], "%Y:%m:%d %H:%M:%S")

        raise Exception(f"Did not find creation date of audio file {file}!")
