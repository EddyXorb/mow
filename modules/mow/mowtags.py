from dataclasses import dataclass
import os
from pathlib import Path
from time import sleep
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

    # the whole gps-machinery of exif is inconsistent.
    # Basiscally, longitude is stored as a positive number and longituderef is either "E" or "W", and both form the longitude. So for every of the three gps-tags, we need to read and write two tags.
    # To ease this, exiftool implements the Composite: prefix, which allows to read and write the gps data as one tag, combining the two tags.
    # Unfortunately, this does not work consistently.
    # E.g. you can read and write longitude to jpg-files, but not to xmp-sidecars when using the Composite: prefix. When using the xmp-prefix this works, but not for altitude.
    # In order to have a consistent behaviour, we need to read and write the two tags separately.
    # To abstract from this, we however define the gps-tags as one tag, and treat them accordingly in the read and write functions.

    gps_latitude = "XMP:GPSLatitude"  # this avoids the need to use the GPSLatitudeRef tag when writing
    gps_longitude = "XMP:GPSLongitude"  # this avoids the need to use the GPSLongitudeRef tag when writing
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
        GPSAltitude = "XMP:GPSAltitude"
        GPSAltitudeRef = "XMP:GPSAltitudeRef"

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

        tags = self._prepare_gps_reading(tags)

        # -n formats the gps output as decimal numbers (for gps data relevant), -struct makes hierarchical data readable as list
        out = self.et.get_tags(
            file, [tag.value for tag in tags], params=["-n", "-struct"]
        )[0]

        read_tags = {tag: out[tag.value] for tag in tags if tag.value in out}

        out = self._convert_to_outer_gps_tags(read_tags)

        return out

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

        if MowTag.sourcefile in tags:
            tags.pop(MowTag.sourcefile)

        if len(tags) == 0:
            return

        if overwrite_original:
            params.append("-overwrite_original")

        tags = self._convert_to_inner_gps_tags(tags)

        self.et.set_tags(
            file,
            {tag.value: value for tag, value in tags.items()},
            params=params,
        )

    def write_to_mediafile(
        self, mFile: MediaFile, tags: dict[MowTag, int | str | float]
    ) -> None:
        """
        Writes tags to all files of the mediafile, including sidecar if present.
        """
        for file in mFile.getAllFileNames():
            self.write_tags(Path(file), tags)

    def write_to_sidecar(
        self, mFile: MediaFile, tags: dict[MowTag, int | str | float]
    ) -> Path:
        """
        Writes to sidecar and adds it to Mediafile if not already present.
        """
        sidecar = Path(mFile.get_sidecar())

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

    def create_sidecar_from_file(
        self,
        mFile: MediaFile,
        ignore_differing_tags: list[MowTag] = [],
    ) -> Path:

        if mFile.has_sidecar():
            raise ValueError("Mediafile already has a sidecar.")

        tags = self._get_combined_file_tags_from(
            mFile, ignore_differing_tags=ignore_differing_tags
        )

        if len(tags) == 0:
            tags = {MowTag.label: "created by mow"}

        self.write_to_sidecar(mFile, tags)

        return Path(mFile.get_sidecar())

    def merge_sidecar_into_mediafile(self, mFile: MediaFile):
        """
        Copies all tags from the sidecar to the file(s) and removes the sidecar.
        """
        sidecar = mFile.get_sidecar()

        tags = self.read_from_sidecar(mFile, tags_all)
        mFile.extensions.remove(".xmp")
        self.write_to_mediafile(mFile, tags)

        sidecar.unlink()

    def _convert_to_inner_gps_tags(
        self, tags: dict[MowTag, str | int | float]
    ) -> dict[MowTag, str | int | float]:
        """special treatment for GPS data, as for reading and writing the needed tags are different
        unfortunately, the gps tags cannot be set using the Composite: prefix.
        We thus need to distinguish between read-only and write-only tags.
        """
        if MowTag.gps_elevation not in tags:
            return tags

        new_tags = tags.copy()

        additional_tags = {}

        if MowTag.gps_elevation in tags:
            additional_tags = {
                self.InternalTag.GPSAltitude: abs(tags[MowTag.gps_elevation]),
                self.InternalTag.GPSAltitudeRef: (
                    0 if tags[MowTag.gps_elevation] >= 0 else 1
                ),
            }
            new_tags.pop(MowTag.gps_elevation)

        new_tags.update(additional_tags)

        return new_tags

    def _convert_to_outer_gps_tags(
        self, tags: dict[MowTag, str | int | float]
    ) -> dict[MowTag, str | int | float]:
        """special treatment for GPS data, as for reading and writing the needed tags are different
        unfortunately, the gps tags cannot be set using the Composite: prefix.
        We thus need to distinguish between read-only and write-only tags.
        """
        new_tags = tags.copy()

        additional_tags = {}

        if self.InternalTag.GPSAltitude in tags:
            additional_tags = {
                MowTag.gps_elevation: (tags[self.InternalTag.GPSAltitude])
            }
            new_tags.pop(self.InternalTag.GPSAltitude)

            if self.InternalTag.GPSAltitudeRef in tags:
                additional_tags[MowTag.gps_elevation] *= (
                    -1 if tags[self.InternalTag.GPSAltitudeRef] == 1 else 1
                )
                new_tags.pop(self.InternalTag.GPSAltitudeRef)

        new_tags.update(additional_tags)

        return new_tags

    def _prepare_gps_reading(self, tags: list[MowTag]) -> list[MowTag]:

        if MowTag.gps_elevation not in tags:
            return tags

        new_tags = tags.copy()

        if MowTag.gps_elevation in tags:
            new_tags += [
                self.InternalTag.GPSAltitude,
                self.InternalTag.GPSAltitudeRef,
            ]
            new_tags.remove(MowTag.gps_elevation)

        return new_tags

    def _get_combined_file_tags_from(
        self,
        mFile: MediaFile,
        ignore_differing_tags: list[MowTag],
    ) -> dict[MowTag, str]:
        tags = {}
        for file in mFile.getAllFileNames():
            new_tags = self.read_tags(file, tags_all)

            if MowTag.sourcefile in new_tags:
                new_tags.pop(MowTag.sourcefile)

            for tag in new_tags.keys():
                if (
                    tag in tags
                    and tags[tag] != new_tags[tag]
                    and tag not in ignore_differing_tags
                ):
                    raise ValueError(
                        f"Tag {tag} has different values in different files of the same media file: {tags[tag]} and {new_tags[tag]}"
                    )

            tags.update(new_tags)
        return tags
