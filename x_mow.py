from modules.general.medialocalizer import BaseLocalizerInput
from modules.mow.mow import Mow
from argparse import ArgumentParser

parser = ArgumentParser(
    "M(edia) flo(OW) - helper to automate media workflow. Needs a working dir to be specified into .mowsettings.yml."
)

subparsers = parser.add_subparsers(dest="command")

copyparser = subparsers.add_parser(
    "copy", help=f"copying media files from external source (1 -> 2)."
)

renameparser = subparsers.add_parser(
    "rename", help=f"transition of renamed media files (2 -> 3)."
)
convertparser = subparsers.add_parser(
    "convert", help="transition of converted media files (3 -> 4)."
)

groupparser = subparsers.add_parser(
    "group",
    help="transition of grouped media files. (4 -> 5). Comes with a bunch of helpers. If one of the helpers is called will not perform transition.",
)

rateparser = subparsers.add_parser(
    "rate", help="transition of rated media files (5.1 -> 5.2)."
)

tagparser = subparsers.add_parser(
    "tag", help="transition of tagged media files (5.2 -> 5.3)."
)

localizeparser = subparsers.add_parser(
    "localize",
    help="transition of localized media files (5.3 -> 6).",
)

aggregateparser = subparsers.add_parser(
    "aggregate", help="transition of aggregated media files (6 -> 7)."
)

statusparser = subparsers.add_parser(
    "status", help="get some status information about the workingdirectory"
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
    help="Expects a comma-separated string such as '^\d*.*,TEST' where the part before the comma is a regex that every file will be searched after and the second part is how matches should be replaced. If given, will just rename mediafiles in place without transitioning them to next stage.",
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
    )
    currentparser.add_argument(
        "-f",
        "--filter",
        help="Only treat files matching this regex (including all subfolders as path).",
        type=str,
        dest="filter",
    )


if __name__ == "__main__":
    args = parser.parse_args()
    if not hasattr(args, "execute"):
        args.execute = False
    if not hasattr(args, "filter"):
        args.filter = ""

    mow = Mow(".mowsettings.yml", dry=not args.execute, filter=args.filter)

    if args.command == "copy":
        mow.copy()
    if args.command == "rename":
        mow.rename(
            useCurrentFilename=args.rename_usecurrent,
            replace=args.rename_replace if args.rename_replace is not None else "",
        )
    if args.command == "convert":
        mow.convert(enforcePassthrough=args.convert_passthrough)
    if args.command == "group":
        mow.group(
            automate=args.group_automate,
            distance=args.group_separate,
            undoAutomatedGrouping=args.group_undogrouping,
            addMissingTimestampsToSubfolders=args.group_timestamps,
            checkSequence=args.group_check_seq,
        )
    if args.command == "rate":
        mow.rate(overrulingfiletype=args.rate_overrule)
    if args.command == "tag":
        mow.tag()
    if args.command == "localize":
        mow.localize(
            localizerInput=BaseLocalizerInput(
                ignoreMissingGpsData=args.localize_ignore_missing_gps_data
            )
        )
    if args.command == "aggregate":
        mow.aggregate(jpgIsSingleSourceOfTruth=args.aggregate_jpgsinglesourceoftruth)
    if args.command == "status":
        mow.status()
