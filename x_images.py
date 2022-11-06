import os
import sys

from general.tkinterhelper import getInputDir

from image.imagerenamer import ImageRenamer
from image.imageclusterer import ImageClusterer
from image.imageparser import parser
from image.imagesearcher import ImageSearcher


def call(args: any):
    if args.all:
        setargsforoption_all(args)
    if args.command == "rename" or args.all:
        executeRenaming(args)
    if args.command == "cluster" or args.all:
        executeClustering(args)
    if args.command == "search":
        executeSearch(args)


def executeSearch(args):
    if args.search_source is None:
        args.search_source = getInputDir(
            "Open search source of files that are expected to be missing."
        )
    if args.search_target is None:
        args.search_target = getInputDir(
            "Open target folder where to look for missing files."
        )

    ImageSearcher(args.search_source, args.search_target, []).findMissingFiles()


def executeClustering(args):
    if args.src is None:
        args.src = getInputDir("Open source")
    if args.all:
        args.move = True
        args.src = os.path.join(args.src, "clustered")

    ImageClusterer(
        src=args.src,
        dst=args.dst,
        hoursmaxdiff=args.diff,
        move=args.move,
        verbose=args.verbose,
        test=args.test,
    )


def executeRenaming(args):
    if args.src is None:
        args.src = getInputDir("Open source")
    if args.dst is None:
        args.dst = os.path.join(args.src, "renamed")
    elif args.dst == "call_filedialog":
        args.dst = getInputDir("Open destination")

    ImageRenamer(
        args.src, args.dst, args.recursive, args.move, args.invert, args.verbose
    )()


def setargsforoption_all(args):
    args.src = getInputDir("Open source")
    args.dst = os.path.join(args.src, "clustered")
    args.diff = 12
    args.move = False
    args.test = False
    args.recursive = False
    args.invert = False


if __name__ == "__main__":
    args = parser.parse_args()
    if len(sys.argv) == 1:  # no args given
        args.all = True
    call(args)
