
import argparse
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