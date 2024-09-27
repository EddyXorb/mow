import os
import sys
from typing import List
import polars as pl
import gpxpy
from zoneinfo import ZoneInfo, available_timezones
import datetime

from ..general.medafilefactories import createAnyValidMediaFile
from .mediatransitioner import MediaTransitioner, TransitionTask, TransitionerInput

TARGET_TIMEZONE = "Europe/Berlin"
INPUT_IMAGE_TIMEZONE = "Europe/Berlin"


@dataclass
class GpsData:
    lat: float
    lon: float
    elev: float


# TODO: add logic for inserting gps data to mediafiles based on given tracks
class MediaLocalizer(MediaTransitioner):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = createAnyValidMediaFile
        super().__init__(input)
        self.positions = self.getAllPositionsDataframe()
        if INPUT_IMAGE_TIMEZONE not in available_timezones():
            print(
                f"Timezone {INPUT_IMAGE_TIMEZONE} is an invalid time zone! Do nothing."
            )
            sys.exit(1)

    def getTasks(self) -> List[TransitionTask]:
        return [TransitionTask(index) for index, _ in enumerate(self.toTreat)]

    def getAllGpxFiles(self) -> List[str]:
        all_files = os.listdir(self.src)
        return [f for f in all_files if f.endswith(".gpx")]

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
        df = df.with_columns(df["time"].dt.convert_time_zone(TARGET_TIMEZONE)).sort(
            "time"
        )
        return df

    def getGpsDataForTime(
        self,
        image_time: datetime.datetime,
        time_offset: datetime.timedelta = datetime.timedelta(seconds=0),
        gps_time_tolerance: datetime.timedelta = datetime.timedelta(seconds=60),
    ) -> GpsData:

        image_time_in_gps_time = self.getNormalizedImageTime(image_time, time_offset)

        before_position, after_position = self.getBeforeAfterGpsData(
            gps_time_tolerance, image_time_in_gps_time
        )

        if len(before_position) > 0 and len(after_position) > 0:
            return self.getInterpolatedGpsData(
                image_time_in_gps_time, before_position, after_position
            )
        elif len(before_position) > 0:
            return GpsData(
                before_position["lat"][0],
                before_position["lon"][0],
                before_position["elevation"][0],
            )
        elif len(after_position) > 0:
            return GpsData(
                after_position["lat"][0],
                after_position["lon"][0],
                after_position["elevation"][0],
            )
        else:
            print(f"No GPS data found for {image_time_in_gps_time}")

        return None

    def getInterpolatedGpsData(self, image_time_in_gps_time, before, after) -> GpsData:
        if after["time"][0] == before["time"][0]:
            return GpsData(before["lat"][0], before["lon"][0], before["elevation"][0])

        ratio = (image_time_in_gps_time - before["time"][0]).total_seconds() / (
            after["time"][0] - before["time"][0]
        ).total_seconds()

        return GpsData(
            lat=(before["lat"] + (after["lat"] - before["lat"]) * ratio)[0],
            lon=(before["lon"] + (after["lon"] - before["lon"]) * ratio)[0],
            elev=(
                before["elevation"] + (after["elevation"] - before["elevation"]) * ratio
            )[0],
        )

    def getNormalizedImageTime(self, image_time, time_offset) -> datetime.datetime:
        image_time_in_gps_time = image_time + time_offset

        if image_time.tzinfo is None:
            image_time_in_gps_time = image_time.replace(
                tzinfo=ZoneInfo(INPUT_IMAGE_TIMEZONE)
            ).astimezone(ZoneInfo(TARGET_TIMEZONE))

        return image_time_in_gps_time

    def getBeforeAfterGpsData(
        self, gps_time_tolerance, image_time_in_gps_time
    ) -> tuple[pl.DataFrame, pl.DataFrame]:

        before = self.positions.filter(
            pl.col("time") < image_time_in_gps_time,
            pl.col("time") >= image_time_in_gps_time - gps_time_tolerance,
        ).tail(1)

        after = self.positions.filter(
            pl.col("time") > image_time_in_gps_time,
            pl.col("time") <= image_time_in_gps_time + gps_time_tolerance,
        ).head(1)

        return before, after
