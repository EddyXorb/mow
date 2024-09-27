# %%
import polars as pl
import gpxpy
from zoneinfo import ZoneInfo, available_timezones
import datetime

GPS_TIME_TOLERANCE = datetime.timedelta(seconds=60)
GPS_TIMEZONE = "Europe/Berlin"


gpx_filepathes = ["test.gpx"]
file_to_gpx_data = {}
for gpx_filepath in gpx_filepathes:
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
# df.write_parquet("test.gpx.parquet", compression="brotli")
#%%

df = df.with_columns(df["time"].dt.convert_time_zone(GPS_TIMEZONE))

image_time = datetime.datetime(2022, 7, 10, 18, 15, 23)
offset = datetime.timedelta(seconds=0)
image_time_in_gps_time = image_time + offset

image_timezone_str = "Europe/Berlin"
if image_time.tzinfo is None:
    if image_timezone_str not in available_timezones():
        print(f"Timezone {image_timezone_str} is an invalid time zone!")
    else:
        image_time_in_gps_time = image_time.replace(
            tzinfo=ZoneInfo(image_timezone_str)
        ).astimezone(ZoneInfo(GPS_TIMEZONE))

df = df.sort("time")
before = df.filter(
    pl.col("time") < image_time_in_gps_time,
    pl.col("time") >= image_time_in_gps_time - GPS_TIME_TOLERANCE,
).tail(1)
after = df.filter(
    pl.col("time") > image_time_in_gps_time,
    pl.col("time") <= image_time_in_gps_time + GPS_TIME_TOLERANCE,
).head(1)

lat = None
lon = None
elev = None

if len(before) > 0 and len(after) > 0:
    if after["time"][0] == before["time"][0]:
        lat = before["lat"][0]
        lon = before["lon"][0]
        elev = before["elevation"][0]
    else:
        ratio = (image_time_in_gps_time - before["time"][0]).total_seconds() / (
            after["time"][0] - before["time"][0]
        ).total_seconds()
    lat = (before["lat"] + (after["lat"] - before["lat"]) * ratio)[0]
    lon = (before["lon"] + (after["lon"] - before["lon"]) * ratio)[0]
    elev = (before["elevation"] + (after["elevation"] - before["elevation"]) * ratio)[0]
elif len(before) > 0:
    lat = before["lat"][0]
    lon = before["lon"][0]
    elev = before["elevation"][0]
elif len(after) > 0:
    lat = after["lat"][0]
    lon = after["lon"][0]
    elev = after["elevation"][0]
else:
    print(f"No GPS data found for {image_time_in_gps_time}")

# %%
