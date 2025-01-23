from dataclasses import dataclass
import os
from pathlib import Path
import sys
import traceback
import polars as pl
import gpxpy
from zoneinfo import ZoneInfo
import zoneinfo
import datetime
import folium

from ..general.mediafile import MediaFile
from ..general.filenamehelper import extractDatetimeFromFileName
from ..mow.mowtags import MowTag, tags_gps_all
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
            MowTag.gps_latitude: self.lat,
            MowTag.gps_longitude: self.lon,
            MowTag.gps_elevation: self.elev,
        }

    def getGPSMetaTagsForReading(self):
        return tags_gps_all

    def fromString(self, s: str):
        parts = s.split(",")
        if len(parts) != 3:
            raise ValueError("Invalid gps data string")
        self.lat = float(parts[0].strip())
        self.lon = float(parts[1].strip())
        self.elev = float(parts[2].strip())

    def __str__(self):
        return f"{self.lat},{self.lon},{self.elev}"


@dataclass
class BaseLocalizerInput:
    time_offset_mediafile: datetime.timedelta = datetime.timedelta(seconds=0)
    gps_time_tolerance_before: datetime.timedelta = datetime.timedelta(seconds=60)
    gps_time_tolerance_after: datetime.timedelta = datetime.timedelta(seconds=60)
    interpolate_linearly: bool = False
    mediafile_timezone: str = "Europe/Berlin"
    force_gps_data: GpsData = None
    transition_even_if_no_gps_data: bool = False
    suppress_map_open: bool = False


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

    def __init__(
        self,
        baselocalizerinput: BaseLocalizerInput,
        transitionerinput: TransitionerInput,
    ):
        BaseLocalizerInput.__init__(self, **baselocalizerinput.__dict__)
        TransitionerInput.__init__(self, **transitionerinput.__dict__)


# TODO: add logic for inserting gps data to mediafiles based on given tracks
class MediaLocalizer(MediaTransitioner):
    def __init__(self, input: LocalizerInput):
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)
        self.gps_time_tolerance_before = input.gps_time_tolerance_before
        self.gps_time_tolerance_after = input.gps_time_tolerance_after
        self.interpolate_linearly = input.interpolate_linearly
        self.time_offset_mediafile = input.time_offset_mediafile
        self.mediafile_timezone = input.mediafile_timezone
        self.force_gps_data = input.force_gps_data
        self.transition_even_if_no_gps_data = input.transition_even_if_no_gps_data
        self.suppress_map_open = input.suppress_map_open

        if self.mediafile_timezone not in zoneinfo.available_timezones():
            self.print_info(
                f"Timezone {self.mediafile_timezone} is an invalid time zone! Do nothing."
            )
            sys.exit(1)

        if self.force_gps_data is None:
            self.positions = self.getAllPositionsDataframe()

    def getTasks(self) -> list[TransitionTask]:
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
                    continue

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
                                skipReason="Could not localize because of missing GPS data.",
                            )
                        )
                        self.print_debug(
                            f"Could not find GPS data for file {Path(mediafile.pathnoext).relative_to(self.src)}, with time {mediafile_time} which was corrected to {self.getNormalizedMediaFileTime(mediafile_time)}"
                        )
                else:
                    self.print_debug(
                        f"Found GPS data for {os.path.basename(mediafile.pathnoext)} : {gps_data}. File has time {mediafile_time}, which was corrected to {self.getNormalizedMediaFileTime(mediafile_time)}"
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
                        skipReason=f"Could not localize {mediafile} because of {e} and {traceback.format_exc()}",
                    )
                )

        self.createMapWithMediafiles(out)

        return out

    def createMapWithMediafiles(self, tasks: list[TransitionTask]):
        fileWithPosition: list[tuple[MediaFile, tuple[float, float]]] = []

        for task in tasks:
            if task.skip:
                continue
            if (
                MowTag.gps_longitude not in task.metaTags
                or MowTag.gps_latitude not in task.metaTags
            ):
                continue
            fileWithPosition.append(
                (
                    self.toTreat[task.index],
                    (
                        task.metaTags[MowTag.gps_latitude],
                        task.metaTags[MowTag.gps_longitude],
                    ),
                )
            )
        if len(fileWithPosition) == 0:
            return

        map = folium.Map(location=fileWithPosition[0][1], zoom_start=5)
        for file, position in fileWithPosition:
            image_path = None
            for extension in file.extensions:
                if extension.upper() in [".JPG", ".JPEG"]:
                    image_path = file.pathnoext + extension
                    break
            if image_path is None:
                folium.Marker(
                    position,
                    tooltip=os.path.basename(file.pathnoext),
                    popup=file.pathnoext.replace("\\", "/"),
                ).add_to(map)
            else:
                image_path = image_path.replace("\\", "/")
                htmlcode = f"""<div>
                        <img src="file://{image_path}" alt="Image" height=400>
                        <br /><span>{os.path.basename(file.pathnoext)}</span>
                        </div>"""
                folium.Marker(
                    position,
                    popup=htmlcode,
                    tooltip=os.path.basename(file.pathnoext),
                ).add_to(map)
        map.fit_bounds(
            [
                [
                    min([pos[0] for _, pos in fileWithPosition]),
                    min([pos[1] for _, pos in fileWithPosition]),
                ],
                [
                    max([pos[0] for _, pos in fileWithPosition]),
                    max([pos[1] for _, pos in fileWithPosition]),
                ],
            ]
        )
        map.save(Path(self.src) / "map.html")

        if not self.suppress_map_open:
            os.startfile(Path(self.src) / "map.html")

    def getAllGpxFiles(self) -> list[str]:
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
            with open(gpx_filepath, "r", encoding="utf-8") as gpx_file:
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
            self.print_info("No GPS data found.")
        return df

    def getGpsDataForTime(
        self,
        mediafile_time: datetime.datetime,
    ) -> GpsData:
        mediafile_time_in_gps_time = self.getNormalizedMediaFileTime(mediafile_time)

        before_position, after_position = self.getBeforeAfterGpsData(
            self.gps_time_tolerance_before,
            self.gps_time_tolerance_after,
            mediafile_time_in_gps_time,
        )

        self.assureElevationExists(before_position, after_position)

        if (
            self.interpolate_linearly
            and before_position is not None
            and after_position is not None
        ):
            return self.getInterpolatedGpsData(
                mediafile_time_in_gps_time, before_position, after_position
            )

        time_diff_before = (
            mediafile_time_in_gps_time - before_position.time
            if before_position is not None
            else datetime.timedelta.max
        )
        time_diff_after = (
            after_position.time - mediafile_time_in_gps_time
            if after_position is not None
            else datetime.timedelta.max
        )

        if before_position is not None and time_diff_before <= time_diff_after:
            return before_position
        elif after_position is not None and time_diff_after <= time_diff_before:
            return after_position
        else:
            return None

    def assureElevationExists(self, before_position, after_position):
        if after_position and before_position:
            if after_position.elev is None and before_position.elev is not None:
                after_position.elev = before_position.elev
            elif before_position.elev is None and after_position.elev is not None:
                before_position.elev = after_position.elev
        else:
            if after_position and after_position.elev is None:
                after_position.elev = 0
            if before_position and before_position.elev is None:
                before_position.elev = 0

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
        self,
        gps_time_tolerance_before: datetime.datetime,
        gps_time_tolerance_after: datetime.datetime,
        mediafile_time_in_gps_time,
    ) -> tuple[GpsData, GpsData]:
        before = self.positions.filter(
            pl.col("time") < mediafile_time_in_gps_time,
            pl.col("time") >= mediafile_time_in_gps_time - gps_time_tolerance_before,
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
            pl.col("time") <= mediafile_time_in_gps_time + gps_time_tolerance_after,
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
