from dataclasses import dataclass
import os
from pathlib import Path
from exiftool import ExifToolHelper
from enum import StrEnum


class MowTags:
    date = "XMP:Date"
    source = "XMP:Source"
    description = "XMP:Description"
    rating = "XMP:Rating"
    subject = "XMP:Subject"
    hierarchicalsubject = "XMP:HierarchicalSubject"
    label = "XMP:Label"
    stagehistory = "XMP:Contributor"

    gps_latitude = "Composite:GPSLatitude"  # this avoids the need to use the GPSLatitudeRef tag when writing
    gps_longitude = "Composite:GPSLongitude"  # this avoids the need to use the GPSLongitudeRef tag when writing

    # unfortunately, the elevation tags cannot be set using the Composite: prefix. We thus need to distinguish between read-only and write-only tags
    gps_elevation_write_only = "GPSAltitude"
    gps_elevationRef_write_only = (
        "GPSAltitudeRef"  # 0 = Above Sea Level, 1 = Below Sea Level
    )
    gps_elevation_read_only = "Composite:GPSAltitude"

    expected = [date, source, description, rating]
    gps_all = [gps_latitude, gps_longitude, gps_elevation_read_only]
    optional = [
        subject,
        hierarchicalsubject,
        label,
        stagehistory,
        *gps_all,
    ]

    all = expected + optional


class MowTag(StrEnum):
    date = "XMP:Date"
    source = "XMP:Source"
    description = "XMP:Description"
    rating = "XMP:Rating"
    subject = "XMP:Subject"
    hierarchicalsubject = "XMP:HierarchicalSubject"
    label = "XMP:Label"
    stagehistory = "XMP:Contributor"

    gps_latitude = "Composite:GPSLatitude"  # this avoids the need to use the GPSLatitudeRef tag when writing
    gps_longitude = "Composite:GPSLongitude"  # this avoids the need to use the GPSLongitudeRef tag when writing
    gps_elevation = "Composite:GPSAltitude"  # _read_only = "Composite:GPSAltitude"


tags_expected = [MowTag.date, MowTag.source, MowTag.description, MowTag.rating]
tags_gps_all = [
    MowTag.gps_latitude,
    MowTag.gps_longitude,
    MowTag.gps_elevation,
]
tags_optional = [
    MowTag.subject,
    MowTag.hierarchicalsubject,
    MowTag.label,
    MowTag.stagehistory,
    *tags_gps_all,
]
tags_all = tags_expected + tags_optional


class MowTagFileManipulator:
    class InternalTag(StrEnum):
        GPSAltitude = "GPSAltitude"
        GPSAltitudeRef = "GPSAltitudeRef"

    def __init__(self):
        self.et = ExifToolHelper()

    def readTags(
        self,
        file: Path,
        tags: list[MowTag],
    ) -> dict[MowTag, str | int | float]:
        """
        File can be any media file, also sidecars.
        """
        out = self.et.get_tags(file, [tag.value for tag in tags])[0]
        return {tag: out[tag.value] for tag in tags if tag.value in out}

    def writeTags(
        self,
        file: Path,
        tags: dict[MowTag, str | int | float],
        overwrite_original: bool = True,
    ):
        """
        File can be any media file, also sidecars.
        """
        params = ["-P", "-L", "-m"]

        if overwrite_original:
            params.append("-overwrite_original")

        tags = self._treat_elevation_writing(tags)

        self.et.set_tags(
            file,
            {tag.value: value for tag, value in tags.items()},
            params=params,
        )

    def write_to_sidecar(
        self, file: Path, tags: dict[MowTag, int | str | float]
    ) -> Path:
        sidecar = file.with_suffix(".xmp")
        self.writeTags(sidecar, tags)
        return sidecar

    def read_from_sidecar(
        self, file: Path, tags: list[MowTag]
    ) -> dict[MowTag, str | int | float]:
        sidecar = file.with_suffix(".xmp")
        return self.readTags(sidecar, tags)

    def create_sidecar_from_file(self, file: Path) -> Path:
        sidecar = file.with_suffix(".xmp")
        tags = self.readTags(file, tags_all)
        self.writeTags(sidecar, tags)
        return sidecar

    def merge_sidecar_into_file(self, file: Path):
        """
        Copies all tags from the sidecar to the file and removes the sidecar.
        """
        sidecar = file.with_suffix(".xmp")
        tags = self.readTags(sidecar, tags_all)
        self.writeTags(file, tags)
        os.remove(sidecar)

    def _treat_elevation_writing(
        self, tags: dict[MowTag, str | int | float]
    ) -> dict[MowTag, str | int | float]:
        """special treatment for GPS elevation, as for reading and writing the needed tags are different
        unfortunately, the elevation tags cannot be set using the Composite: prefix.
        We thus need to distinguish between read-only and write-only tags.
        """

        if MowTag.gps_elevation not in tags:
            return tags

        new_tags = tags.copy()
        additional_tags = {
            self.InternalTag.GPSAltitude: abs(tags[MowTag.gps_elevation]),
            self.InternalTag.GPSAltitudeRef: (
                0 if tags[MowTag.gps_elevation] >= 0 else 1
            ),
        }
        new_tags.update(additional_tags)
        new_tags.pop(MowTag.gps_elevation)

        return new_tags
