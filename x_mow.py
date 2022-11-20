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
    "group",
    help="Execute grouping of media files. (Transition 4 -> 5). Comes with a bunch of helpers. If one of the helpers is called will not perform transition.",
)

rateparser = subparsers.add_parser(
    "rate", help="Execute transition of rated media files (Transition 5.1 -> 5.2))"
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

renameparser.add_argument(
    "-x",
    "--execute",
    help="Really execute moving/renaming of files/folders, not only in dry mode. Since the renaming features are powerful we do not want it to be the default behavior that something is really done.",
    dest="rename_execute",
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
    "-x",
    "--execute",
    help="Really execute moving/renaming of files/folders, not only in dry mode. Since the grouping features are powerful we do not want it to be the default behavior that something is really done.",
    dest="group_execute",
    action="store_true",
)

rateparser.add_argument(
    "-x",
    "--execute",
    help="Really execute moving/renaming of files/folders, not only in dry mode, which is default.",
    action="store_true",
    dest="rate_execute"
)


if __name__ == "__main__":
    args = parser.parse_args()
    mow = Mow(".mowsettings.yml")

    if args.command == "rename":
        mow.rename(
            useCurrentFilename=args.rename_usecurrent,
            replace=args.rename_replace if args.rename_replace is not None else "",
            dry=not args.rename_execute,
        )
    if args.command == "convert":
        mow.convert()
    if args.command == "group":
        mow.group(
            automate=args.group_automate,
            distance=args.group_separate,
            dry=not args.group_execute,
            undoAutomatedGrouping=args.group_undogrouping,
            addMissingTimestampsToSubfolders=args.group_timestamps,
        )
    if args.command == "rate":
        mow.rate(dry = not args.rate_execute)
