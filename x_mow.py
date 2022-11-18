from modules.mow.mow import Mow
from argparse import ArgumentParser

parser = ArgumentParser(
    "M(edia) flo(OW) - helper to automate media workflow. Needs a working dir to be specified into .mowsettings.yml."
)

subparsers = parser.add_subparsers(dest="command")

renameparser = subparsers.add_parser(
    "rename", help="Execute renaming of media files (Transition 2 -> 3)."
)
convertparser = subparsers.add_parser(
    "convert", help="Execute conversion of media files. (Transition 3 -> 4)"
)

groupparser = subparsers.add_parser(
    "group", help="Execute grouping of media files. (Transition 4 -> 5)"
)


renameparser.add_argument(
    "-c",
    "--usecurrentfilename",
    help="Files are not renamed and their filename is supposed to be already in the correct format (YYYY-MM-DD@HHMMSS_#). The given date is taken as source of truth for the further processes (e.g. XMP-data).",
    action="store_true",
    dest="rename_usecurrent",
)

groupparser.add_argument(
    "-a",
    "--automate",
    help="Group ungrouped files, e.g. those that are directly in 'group' folder. Will however add prefix 'TODO_'",
    dest="group_automate",
    action="store_true",
)

groupparser.add_argument(
    "-s",
    "--separation",
    help="If grouping ungrouped (-g), will separate files with timediff > this value in hours.",
    dest="group_separate",
    type=int,
    default=8,
)

groupparser.add_argument(
    "-d",
    "--dry",
    help="Don't actually group anything, but print what would be done.",
    dest="group_dry",
    action="store_true",
)

if __name__ == "__main__":
    args = parser.parse_args()
    mow = Mow(".mowsettings.yml")

    print(args)

    if args.command == "rename":
        mow.rename(useCurrentFilename=args.rename_usecurrent)
    if args.command == "convert":
        mow.convert()
    if args.command == "group":
        mow.group(
            automate=args.group_automate,
            distance=args.group_separate,
            dry=args.group_dry,
        )
