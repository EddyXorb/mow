import datetime
import re
from modules.general.medialocalizer import BaseLocalizerInput, GpsData
from modules.mow.mow import Mow
from argparse import ArgumentParser, Namespace

parser = ArgumentParser(
    "M(edia) flo(OW) - helper to automate media workflow. Needs a working dir to be specified into .mowsettings.yml."
)

subparsers = parser.add_subparsers(dest="command")

command_aliases = {
    "copy": ["cop"],
    "rename": ["ren"],
    "convert": ["con"],
    "group": ["grp"],
    "rate": ["rat"],
    "tag": [],
    "localize": ["loc"],
    "aggregate": ["agg"],
    "status": ["sta"],
}

copyparser = subparsers.add_parser(
    "copy",
    help="copying media files from external source (1 -> 2).",
    aliases=command_aliases["copy"],
)

renameparser = subparsers.add_parser(
    "rename",
    help="transition of renamed media files (2 -> 3).",
    aliases=command_aliases["rename"],
)
convertparser = subparsers.add_parser(
    "convert",
    help="transition of converted media files (3 -> 4).",
    aliases=command_aliases["convert"],
)

groupparser = subparsers.add_parser(
    "group",
    help="transition of grouped media files. (4 -> 5). Comes with a bunch of helpers. If one of the helpers is called will not perform transition.",
    aliases=command_aliases["group"],
)

rateparser = subparsers.add_parser(
    "rate",
    help="transition of rated media files (5.1 -> 5.2).",
    aliases=command_aliases["rate"],
)

tagparser = subparsers.add_parser(
    "tag",
    help="transition of tagged media files (5.2 -> 5.3).",
    aliases=command_aliases["tag"],
)

localizeparser = subparsers.add_parser(
    "localize",
    help="transition of localized media files (5.3 -> 6).",
    aliases=command_aliases["localize"],
)

aggregateparser = subparsers.add_parser(
    "aggregate",
    help="transition of aggregated media files (6 -> 7).",
    aliases=command_aliases["aggregate"],
)

statusparser = subparsers.add_parser(
    "status",
    help="get some status information about the workingdirectory",
    aliases=command_aliases["status"],
)

renameparser.add_argument(
    "-c",
    "--usecurrentfilename",
    help="Files are not renamed and their filename is supposed to be already in the correct format (YYYY-MM-DD@HHMMSS_#). The given date is taken as source of truth for the further processes (e.g. XMP-data).",
    action="store_true",
    dest="rename_usecurrent",
)

renameparser.add_argument(
    "-r",
    "--replace",
    help="Expects a comma-separated string such as '^\\d*.*,TEST' where the part before the comma is a regex that every file will be searched after and the second part is how matches should be replaced. If given, will just rename mediafiles in place without transitioning them to next stage.",
    type=str,
    dest="rename_replace",
)

convertparser.add_argument(
    "-p",
    "--passthrough",
    help="Enforces pasthrough for all files.",
    dest="convert_passthrough",
    action="store_true",
)

convertparser.add_argument(
    "-j",
    "--jpg-quality",
    help="Quality of jpg files, range in [1,100]. Default is 100. If 100, no compression is applied to jpg-files.",
    type=int,
    default=100,
    choices=range(1, 101),
    dest="convert_jpg_quality",
    metavar="QUALITY",
)

groupparser.add_argument(
    "-a",
    "--automate",
    help="Group ungrouped files, e.g. those that are directly in 'group' folder. Will however add prefix 'TODO_'. Nothing else is done then.",
    dest="group_automate",
    action="store_true",
)

groupparser.add_argument(
    "-s",
    "--separation",
    help="If --automate active, will separate files with timediff > this value in hours. Default is 8.",
    dest="group_separate",
    type=int,
    default=8,
)

groupparser.add_argument(
    "-u",
    "--undogrouping",
    help="Undo grouping which was executed by --automate. Nothing else is done then.",
    dest="group_undogrouping",
    action="store_true",
)

groupparser.add_argument(
    "-t",
    "--timestamps",
    help="Add missing timestamps to folders in group folder. Nothing else is done then.",
    dest="group_timestamps",
    action="store_true",
)

groupparser.add_argument(
    "-c",
    "--check-seq",
    help="Checks if grouped files are in their respective groups, i.e. if there are two groups A, B and the timestamp from A < B, then check is okay iff  every timestamp of every mediafile x in A is smaller than timestamp of B.",
    dest="group_check_seq",
    action="store_true",
)

rateparser.add_argument(
    "-o",
    "--overrule",
    help="Overrules conflicting ratings with rating for given fileending, if existent. E.g. if --overrule jpg is set, then the rating of a jpg will be taken as source of truth for the rating of the raw-file.",
    dest="rate_overrule",
    type=str,
    default=None,
)

localizeparser.add_argument(
    "-i",
    "--ignore_missing_gps_data",
    help="If set, will transition files even if they do not have GPS data.",
    action="store_true",
    dest="localize_ignore_missing_gps_data",
    default=False,
)

localizeparser.add_argument(
    "-o",
    "--time_offset_mediafile",
    help="Time offset for media files. E.g. if the cameras time is 10 seconds in the future, you can correct it by writing -o=-10s. General format: -o=1h30m15s.",
    type=str,
    dest="localize_time_offset_mediafile",
)

localizeparser.add_argument(
    "-t",
    "--gps_time_tolerance",
    help="Time tolerance for GPS data. General format: -t=1h30m15s. If a mediafiles timestamp is within this tolerance of a GPS data timestamp, the GPS data is taken as source of truth for the mediafile.",
    type=str,
    dest="localize_gps_time_tolerance",
    default="10m",
)

localizeparser.add_argument(
    "-z",
    "--timezone",
    help="Timezone of the mediafiles. Default is Europe/Berlin. To see all available timezones, see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
    type=str,
    dest="localize_timezone",
    default="Europe/Berlin",
)

localizeparser.add_argument(
    "--force_gps_data",
    help="Force GPS data. If set, all files get assigned this gps data, independently of gpx information available. Format: --force-gps-data -12,34.45,4556, interpreted as latitude,longitude,height.",
    type=str,
    dest="localize_force_gps_data",
)

localizeparser.add_argument(
    "-s",
    "--suppress-map-open",
    help="Do not open a map with the found GPS data after calling the localizer, which is the default.",
    action="store_true",
    dest="localize_suppress_map_open",
    default=False,
)


aggregateparser.add_argument(
    "-j",
    "--jpg-single-source-of-truth",
    help="If set, the tags that are contained in jpgs (including ratings) are taken only from jpg. This will overwrite any different tags set on the raw-file, if present.",
    action="store_true",
    dest="aggregate_jpgsinglesourceoftruth",
)

stageparsers = [
    copyparser,
    renameparser,
    convertparser,
    rateparser,
    tagparser,
    groupparser,
    localizeparser,
    aggregateparser,
]
for currentparser in stageparsers:
    currentparser.add_argument(
        "-x",
        "--execute",
        help="Really execute moving/renaming of files/folders, not only in dry mode. Since the grouping features are powerful we do not want it to be the default behavior that something is really done.",
        dest="execute",
        action="store_true",
        default=False,
    )
    currentparser.add_argument(
        "-f",
        "--filter",
        help="Only treat files matching this regex (including all subfolders as path).",
        type=str,
        dest="filter",
        default="",
        metavar="REGEX",
    )
    currentparser.add_argument(
        "-l",
        "--list",
        help="List items in current stage waiting for treatment. Will print only first 100.",
        action="store_true",
        dest="list",
        default=False,
    )
    currentparser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        help="Set minimal verbosity level for logging. 0 = CRITICAL, 1 = ERROR, 2 = WARNING, 3 = INFO (default), 4 = DEBUG",
        default=3,
        metavar="LEVEL",
        dest="verbosity",
    )


def parse_timedelta(time_str) -> datetime.timedelta:
    # Define the regex pattern to match hours, minutes, and seconds
    pattern = r"(-)?(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?"
    match = re.match(pattern, time_str)

    if not match:
        raise ValueError(f"Invalid time format: {time_str}")

    sign = -1 if match.group(1) else 1
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    seconds = int(match.group(4)) if match.group(4) else 0

    return datetime.timedelta(
        hours=sign * hours, minutes=sign * minutes, seconds=sign * seconds
    )


def should_execute_stage(stage: str, args: Namespace):
    return stage == args.command or args.command in command_aliases[stage]


def get_canonical_command(command: str):
    for key, value in command_aliases.items():
        if command in value:
            return key
        if command == key:
            return key
    return command


def main():
    args = parser.parse_args()

    mow = Mow(
        ".mowsettings.yml",
        dry=not args.execute if hasattr(args, "execute") else True,
        filter=args.filter if hasattr(args, "filter") else "",
        verbosity=args.verbosity if hasattr(args, "verbosity") else 3,
    )

    if hasattr(args, "list") and args.list:
        mow.list_todos(stage=get_canonical_command(args.command))
    elif should_execute_stage("copy", args):
        mow.copy()
    elif should_execute_stage("rename", args):
        mow.rename(
            useCurrentFilename=args.rename_usecurrent,
            replace=args.rename_replace if args.rename_replace is not None else "",
        )
    elif should_execute_stage("convert", args):
        mow.convert(
            enforcePassthrough=args.convert_passthrough,
            jpg_quality=args.convert_jpg_quality,
        )
    elif should_execute_stage("group", args):
        mow.group(
            automate=args.group_automate,
            distance=args.group_separate,
            undoAutomatedGrouping=args.group_undogrouping,
            addMissingTimestampsToSubfolders=args.group_timestamps,
            checkSequence=args.group_check_seq,
        )
    elif should_execute_stage("rate", args):
        mow.rate(overrulingfiletype=args.rate_overrule)
    elif should_execute_stage("tag", args):
        mow.tag()
    elif should_execute_stage("localize", args):
        inp = BaseLocalizerInput(
            transition_even_if_no_gps_data=args.localize_ignore_missing_gps_data,
            mediafile_timezone=args.localize_timezone,
        )
        if args.localize_time_offset_mediafile is not None:
            inp.time_offset_mediafile = parse_timedelta(
                args.localize_time_offset_mediafile
            )
        if args.localize_gps_time_tolerance is not None:
            inp.gps_time_tolerance = parse_timedelta(args.localize_gps_time_tolerance)
        if args.localize_force_gps_data is not None:
            inp.force_gps_data = GpsData.fromString(args.localize_force_gps_data)
        if args.localize_suppress_map_open:
            inp.suppress_map_open = True

        mow.localize(localizerInput=inp)
    elif should_execute_stage("aggregate", args):
        mow.aggregate(jpgIsSingleSourceOfTruth=args.aggregate_jpgsinglesourceoftruth)
    elif should_execute_stage("status", args):
        mow.status()


if __name__ == "__main__":
    main()
