from modules.mow.mow import Mow
from argparse import ArgumentParser

parser = ArgumentParser(
    "M(edia) flo(OW) - helper to automate media workflow. Needs a working dir to be specified into .mowsettings.yml."
)

subparsers = parser.add_subparsers(dest="command")

renameparser = subparsers.add_parser("rename", help="Execute renaming of media files (Transition 2 -> 3).")
convertparser = subparsers.add_parser(
    "convert", help="Execute conversion of media files. (Transition 3 -> 4)"
)


renameparser.add_argument(
    "-c",
    "--usecurrentfilename",
    help="Files are not renamed and their filename is supposed to be already in the correct format (YYYY-MM-DD@HHMMSS_#). The given date is taken as source of truth for the further processes (e.g. XMP-data).",
    action="store_true",
    dest="rename_usecurrent",
)

if __name__ == "__main__":
    args = parser.parse_args()
    mow = Mow(".mowsettings.yml")

    if args.command == "rename":
        mow.rename(useCurrentFilename=args.rename_usecurrent)
    if args.command == "convert":
        mow.convert()
