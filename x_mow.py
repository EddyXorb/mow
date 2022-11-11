from modules.mow.mow import Mow
from argparse import ArgumentParser

parser = ArgumentParser(
    "M(edia) flo(OW) - helper to automate media workflow. Needs a working dir to be specified into .mowsettings.yml."
)
parser.add_argument(
    "-r", "--rename", help="execute renaming", action="store_true", dest="rename"
)

parser.add_argument(
    "-c", "--convert", help="execute conversion", action="store_true", dest="convert"
)

if __name__ == "__main__":
    args = parser.parse_args()
    mow = Mow(".mowsettings.yml")

    if args.rename:
        mow.rename()
    if args.convert:
        mow.convert()
