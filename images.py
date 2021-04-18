import argparse
import os
import sys

from image.imagerenamer import ImageRenamer
from image.imageclusterer import ImageClusterer

parser = argparse.ArgumentParser("Images")

parser.add_argument("-v", "--verbose", help="print more output", action="store_true")
parser.add_argument(
    "-a",
    "--all",
    help="perform image renaming and clustering in one step with default parameters. Asks for directory.",
    action="store_true",
)

subparsers = parser.add_subparsers(help="commands", dest="command")
renameparser = subparsers.add_parser("rename")
clusterparser = subparsers.add_parser("cluster")

renameparser.add_argument("-s", "--src", help="source dir", type=str)
renameparser.add_argument(
    "-d",
    "--dst",
    help="destination dir. Must be different from src. If not specified, takes src/renamed.",
    type=str,
    const="call_filedialog",
    nargs="?",
)
renameparser.add_argument("-r", "--recursive", action="store_true")
renameparser.add_argument(
    "-m",
    "--move",
    action="store_true",
    help="if true, moves files instead of copying them.",
)
renameparser.add_argument(
    "-i",
    "--invert",
    help="invert renaming direction, causing already renamed files to get their old names back.",
    action="store_true",
)


clusterparser.add_argument(
    "-s", "--src", help="source folder containing files to be clustered", type=str
)

clusterparser.add_argument(
    "-d", "--dst", help="destination folder containing clustered files", type=str
)

clusterparser.add_argument(
    "-m",
    "--move",
    help="if true, images will be moved into new locations instead of copied.",
    action="store_true",
)
clusterparser.add_argument(
    "--diff",
    help="if two images have a creation time whose timedifference in hours is smaller than this value, they will belong to the same cluster else not.",
    default=24,
    type=int,
)

clusterparser.add_argument(
    "-t",
    "--test",
    help="if set, print only what would be done.",
    action="store_true",
)


def getInputDir(title: str = "open") -> str:
    from tkinter import filedialog
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title=title)
    if not os.path.isdir(folder):
        print("No dir specified, do nothing.")
        sys.exit()
    return folder


def call(args: any):
    renamer = None

    if args.all:
        args.src = getInputDir("Open source")
        args.dst = os.path.join(args.src, "clustered")
        args.diff = 24
        args.move = False
        args.test = False
        args.recursive = False
        args.invert = False

    if args.command == "rename" or args.all:
        if args.src is None:
            args.src = getInputDir("Open source")
        if args.dst is None:
            args.dst = os.path.join(args.src, "renamed")
        elif args.dst == "call_filedialog":
            args.dst = getInputDir("Open destination")

        ImageRenamer(
            args.src, args.dst, args.recursive, args.move, args.invert, args.verbose
        )

    if args.command == "cluster" or args.all:
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


if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
    call(args)
