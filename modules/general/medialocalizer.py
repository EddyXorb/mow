from dataclasses import dataclass
import os
import sys
import traceback
from typing import List
import polars as pl
import gpxpy
from zoneinfo import ZoneInfo, available_timezones
import datetime

from ..general.filenamehelper import extractDatetimeFromFileName
from ..mow.mowtags import MowTags
from ..general.medafilefactories import createAnyValidMediaFile
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput

INTERNAL_BASE_TIMEZONE = "UTC"


@dataclass
class GpsData:
    lat: float
    lon: float
    elev: float
    time: datetime.datetime = None  # time is optional

    def getGPSMetaTagsForWriting(self):
        return {
            MowTags.gps_latitude: self.lat,
            MowTags.gps_longitude: self.lon,
            MowTags.gps_elevation_write_only: self.elev,
            MowTags.gps_elevationRef_write_only: 0 if self.elev >= 0 else 1,
        }

    def getGPSMetaTagsForReading(self):
        return MowTags.gps_all


@dataclass
class BaseLocalizerInput:
    time_offset_mediafile: datetime.timedelta = datetime.timedelta(seconds=0)
    gps_time_tolerance: datetime.timedelta = datetime.timedelta(seconds=60)
    mediafile_timezone: str = "Europe/Berlin"
    force_gps_data: GpsData = None
    transition_even_if_no_gps_data: bool = False
    print_found_gps_coordinates: bool = False


class LocalizerInput(BaseLocalizerInput, TransitionerInput):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for mediafiles
    dry: don't actually change anything, just show what would be done
    writeMetaTags: sets GPS data in media files
    time_offset_mediafile: timedelta, enforced time offset for mediafile to create congruence to gps time (e.g. if camera time is 1 hour ahead of gps time, set this to +1 hour. This the case if we are in Europe/Berlin=UTC+1 (gps is always UTC time)).
    gps_time_tolerance: timedelta, time tolerance for gps data. If no gps data is found within this time range, no gps data will be inserted into the media file.
    mediafile_timezone: str, timezone of the mediafiles. This is used to convert the mediafiles time to the gps time. The mediafile time is taken from the filename, so no metainformation is taken into account (e.g. from Date Time UTC-Flag in JPGs) If the timezone is not given, the timezone "Europe/Berlin" is used.
    force_gps_data: GpsData, if given, this gps data will be inserted into every media file. In this case, all files will be transitioned.
    transition_even_if_no_gps_data: bool, if true, the mediafile will be transitioned even if no gps data was found. In this case, the mediafile will be transitioned without gps data.
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# TODO: add logic for inserting gps data to mediafiles based on given tracks
class MediaLocalizer(MediaTransitioner):
    def __init__(self, input: LocalizerInput):

        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)
        self.gps_time_tolerance = input.gps_time_tolerance
        self.time_offset_mediafile = input.time_offset_mediafile
        self.mediafile_timezone = input.mediafile_timezone
        self.force_gps_data = input.force_gps_data
        self.transition_even_if_no_gps_data = input.transition_even_if_no_gps_data
        self.print_found_gps_coordinates = input.print_found_gps_coordinates

        if self.mediafile_timezone not in available_timezones():
            self.printv(
                f"Timezone {self.mediafile_timezone} is an invalid time zone! Do nothing."
            )
            sys.exit(1)

        self.positions = self.getAllPositionsDataframe()

    def getTasks(self) -> List[TransitionTask]:
        out = []
        for index, mediafile in enumerate(self.toTreat):
            try:
                if self.force_gps_data is not None:
                    out.append(
                        TransitionTask(
                            index,
                            metaTags=self.force_gps_data.getGPSMetaTagsForWriting(),
                        )
                    )
                else:
                    mediafile_time = extractDatetimeFromFileName(mediafile.pathnoext)
                    gps_data = self.getGpsDataForTime(mediafile_time)

                    if gps_data is None:
                        if self.transition_even_if_no_gps_data:
                            out.append(TransitionTask(index))
                        else:
                            out.append(
                                TransitionTask(
                                    index,
                                    skip=True,
                                    skipReason=f"Could not localize {mediafile} because of missing GPS data. File has time {mediafile_time}, which was corrected to {self.getNormalizedMediaFileTime(mediafile_time)}",
                                )
                            )
                    else:
                        if self.print_found_gps_coordinates:
                            self.printv(
                                f"Found GPS data for {mediafile}:{gps_data}. File has time {mediafile_time}, which was corrected to {self.getNormalizedMediaFileTime(mediafile_time)}"
                            )
                        out.append(
                            TransitionTask(
                                index, metaTags=gps_data.getGPSMetaTagsForWriting()
                            )
                        )
            except Exception as e:
                out.append(
                    TransitionTask(
                        index,
                        skip=True,
                        skipReason=f"Could not localize {mediafile} because of {e}",
                    )
                )

        return out

    def getAllGpxFiles(self) -> List[str]:
        all_files = os.listdir(self.src)
        return [
            os.path.abspath(os.path.join(self.src, f))
            for f in all_files
            if f.endswith(".gpx")
        ]

    def getAllPositionsDataframe(self) -> pl.DataFrame:
        gpx_files = self.getAllGpxFiles()
        file_to_gpx_data = {}

        for gpx_filepath in gpx_files:
            with open(gpx_filepath, "r") as gpx_file:
                file_to_gpx_data[gpx_filepath] = gpxpy.parse(gpx_file)

        rawPositions = {"time": [], "lat": [], "lon": [], "elevation": [], "file": []}

        for gpx_filepath, gpx_data in file_to_gpx_data.items():
            for track in gpx_data.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        rawPositions["time"].append(point.time)
                        rawPositions["lat"].append(point.latitude)
                        rawPositions["lon"].append(point.longitude)
                        rawPositions["elevation"].append(point.elevation)
                        rawPositions["file"].append(gpx_filepath)

        df = pl.DataFrame(rawPositions)
        if len(df) != 0:
            df = df.with_columns(
                df["time"].dt.convert_time_zone(INTERNAL_BASE_TIMEZONE)
            ).sort("time")
        else:
            self.printv("No GPS data found.")
        return df

    def getGpsDataForTime(
        self,
        mediafile_time: datetime.datetime,
    ) -> GpsData:

        mediafile_time_in_gps_time = self.getNormalizedMediaFileTime(mediafile_time)

        before_position, after_position = self.getBeforeAfterGpsData(
            self.gps_time_tolerance, mediafile_time_in_gps_time
        )

        if before_position is not None and after_position is not None:
            return self.getInterpolatedGpsData(
                mediafile_time_in_gps_time, before_position, after_position
            )
        elif before_position is not None:
            return before_position
        elif after_position is not None:
            return after_position
        else:
            return None

    def getInterpolatedGpsData(
        self, mediafile_time_in_gps_time, before: GpsData, after: GpsData
    ) -> GpsData:

        if after.time == before.time:
            return before

        ratio = (mediafile_time_in_gps_time - before.time).total_seconds() / (
            after.time - before.time
        ).total_seconds()

        return GpsData(
            lat=before.lat + (after.lat - before.lat) * ratio,
            lon=before.lon + (after.lon - before.lon) * ratio,
            elev=before.elev + (after.elev - before.elev) * ratio,
            time=mediafile_time_in_gps_time,
        )

    def getNormalizedMediaFileTime(self, mediafile_time) -> datetime.datetime:
        mediafile_time_in_gps_time = mediafile_time + self.time_offset_mediafile

        if mediafile_time.tzinfo is None:
            mediafile_time_in_gps_time = mediafile_time_in_gps_time.replace(
                tzinfo=ZoneInfo(self.mediafile_timezone)
            )

        mediafile_time_in_gps_time = mediafile_time_in_gps_time.astimezone(
            ZoneInfo(INTERNAL_BASE_TIMEZONE)
        )
        return mediafile_time_in_gps_time

    def getBeforeAfterGpsData(
        self, gps_time_tolerance, mediafile_time_in_gps_time
    ) -> tuple[pl.DataFrame, pl.DataFrame]:

        before = self.positions.filter(
            pl.col("time") < mediafile_time_in_gps_time,
            pl.col("time") >= mediafile_time_in_gps_time - gps_time_tolerance,
        ).tail(1)

        if len(before) > 0:
            before = GpsData(
                lat=before["lat"][0],
                lon=before["lon"][0],
                elev=before["elevation"][0],
                time=before["time"][0],
            )
        else:
            before = None

        after = self.positions.filter(
            pl.col("time") > mediafile_time_in_gps_time,
            pl.col("time") <= mediafile_time_in_gps_time + gps_time_tolerance,
        ).head(1)

        if len(after) > 0:
            after = GpsData(
                lat=after["lat"][0],
                lon=after["lon"][0],
                elev=after["elevation"][0],
                time=after["time"][0],
            )
        else:
            after = None

        return before, after
