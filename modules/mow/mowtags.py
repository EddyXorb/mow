from dataclasses import dataclass
import os
from pathlib import Path
from exiftool import ExifToolHelper
from enum import StrEnum

from ..general.mediafile import MediaFile


class MowTag(StrEnum):
    date = "XMP:Date"
    source = "XMP:Source"
    description = "XMP:Description"
    rating = "XMP:Rating"
    subject = "XMP:Subject"
    hierarchicalsubject = "XMP:HierarchicalSubject"
    label = "XMP:Label"
    stagehistory = "XMP:Contributor"
    sourcefile = "SourceFile"  # this is a special tag, as it is not an XMP tag and it contains the filename of the file where the meta tag comes from

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
    MowTag.sourcefile,
    *tags_gps_all,
]
tags_all = tags_expected + tags_optional


class MowTagFileManipulator:
    class InternalTag(StrEnum):
        GPSAltitude = "GPSAltitude"
        GPSAltitudeRef = "GPSAltitudeRef"

    def __init__(self):
        self.et = ExifToolHelper()

    def read_tags(
        self,
        file: Path,
        tags: list[MowTag],
    ) -> dict[MowTag, str | int | float]:
        """
        File can be any media file, also sidecars. This is the basic read function; every other read function should call this one.
        """
        out = self.et.get_tags(
            file, [tag.value for tag in tags], params=["-n", "-struct"]
        )[
            0
        ]  # -n formats the gps output as decimal numbers (for gps data relevant)
        return {tag: out[tag.value] for tag in tags if tag.value in out}

    def write_tags(
        self,
        file: Path,
        tags: dict[MowTag, str | int | float],
        overwrite_original: bool = True,
    ):
        """
        File can be any media file, also sidecars. This is the basic write function; every other write function should call this one.
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
        self, mFile: MediaFile, tags: dict[MowTag, int | str | float]
    ) -> Path:
        """
        Writes to sidecar and adds it to Mediafile if not already present.
        """
        sidecar = Path(mFile.pathnoext + ".xmp")
        self.write_tags(sidecar, tags)
        if not mFile.has_sidecar():
            mFile.extensions.append(sidecar.suffix)
        return sidecar

    def read_from_sidecar(
        self, file: MediaFile, tags: list[MowTag]
    ) -> dict[MowTag, str | int | float]:

        sidecar = file.get_sidecar()
        if os.path.exists(sidecar):
            return self.read_tags(sidecar, tags)

        raise FileNotFoundError(f"No sidecar found for {file}")

    def create_sidecar_from_file(self, mFile: MediaFile) -> Path:

        if mFile.has_sidecar():
            raise ValueError("Mediafile already has a sidecar.")

        tags = self._get_combined_file_tags_from(mFile)
        sidecar = Path(mFile.get_sidecar())
        self.write_tags(sidecar, tags)
        mFile.extensions.append(".xmp")

        return sidecar

    def merge_sidecar_into_mediafile(self, mFile: MediaFile):
        """
        Copies all tags from the sidecar to the file(s) and removes the sidecar.
        """
        if not mFile.has_sidecar():
            return

        sidecar = mFile.get_sidecar()
        tags = self.read_tags(sidecar, tags_all)

        for file in mFile.getAllFileNames():
            if file == sidecar:
                continue

            self.write_tags(file, tags)

        mFile.extensions.remove(".xmp")
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

    def _get_combined_file_tags_from(self, mFile: MediaFile) -> dict[MowTag, str]:
        tags = {}
        for file in mFile.getAllFileNames():
            new_tags = self.read_tags(file, tags_all)

            for tag in new_tags.keys():
                if tag == MowTag.sourcefile:
                    continue
                if tag in tags and tags[tag] != new_tags[tag]:
                    raise ValueError(
                        f"Tag {tag} has different values in different files of the same media file: {tags[tag]} and {new_tags[tag]}"
                    )

            tags.update(new_tags)
        return tags
