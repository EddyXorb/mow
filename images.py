from image.imagerenamer import ImageRenamer

import argparse
import os
import sys


parser = argparse.ArgumentParser("Images")
subparsers = parser.add_subparsers(help="commands", dest="command")
renameparser = subparsers.add_parser("rename")

renameparser.add_argument("-s", "--src", help="source dir", type=str)
renameparser.add_argument(
    "-d",
    "--dst",
    help="destination dir. Must be different from src. If not specified, takes src/renamed.",
    type=str,
)
renameparser.add_argument("-r", "--recursive", action="store_true")
renameparser.add_argument(
    "-m",
    "--move",
    action="store_true",
    help="if true, moves files instead of copying them.",
)

renameparser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="more output.",
)

renameparser.add_argument(
    "-i",
    "--invert",
    help="invert renaming direction, causing already renamed files to get their old names back.",
    action="store_true",
)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.command == "rename":
        if args.src is None:
            from tkinter import filedialog
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            args.src = filedialog.askdirectory()
            if not os.path.isdir(args.src):
                print("No dir specified, do nothing.")
                sys.exit()
        if args.dst is None:
            args.dst = os.path.join(args.src, "renamed")

        ImageRenamer(args.src, args.dst, args.recursive, args.move, args.invert, args.verbose)
