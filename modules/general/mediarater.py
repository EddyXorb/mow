from dataclasses import dataclass
from typing import List

from ..general.mediafile import MediaFile
from .mediatransitioner import MediaTransitioner, TansitionerInput
from ..general.medafilefactories import createAnyValidMediaFile

from exiftool import ExifToolHelper


@dataclass(kw_only=True)
class RaterInput(TansitionerInput):
    transitionPartiallyRatedGroups = False


class MediaRater(MediaTransitioner):
    def __init__(self, input: RaterInput):
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)
        self.transitionPartiallyRatedGroups = input.transitionPartiallyRatedGroups

    def getRatedMediaFileIndices(self) -> List[int]:
        with ExifToolHelper() as et:
            tags = et.get_tags([str(file) for file in self.toTreat], "xmp:rating")
            return [
                index
                for index, _ in enumerate(self.toTreat)
                if "XMP:Rating" in tags[index]
            ]
        
    
