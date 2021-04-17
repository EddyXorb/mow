
from tkinter.constants import MULTIPLE
from transcodevideo import Transcoder
from subprocess import run
import argparse
import os
import re
from pathlib import Path
from tkinter import filedialog
import tkinter as tk
import time

root = tk.Tk()
root.withdraw()

parser = argparse.ArgumentParser("MovTranscoder")

parser.add_argument(
    "-i",
    "--input",
    help="define root folder to search for movs. Converts all videos found and puts them into subfolder 'videos'",
    type=str,
    nargs="?",
    default="NULL",
)

parser.add_argument(
    "-q", "--quality", type=str, choices=["hd", "sd", "android"], default="hd"
)


class MovTranscoder:
    def __init__(self, root: str, quality: str):
        self.root = os.path.abspath(root)
        self.quality = quality
        self.transcoded = {}
        print("Transcode all .MOV-files in " + self.root)

    def __call__(self):
        for root, dirs, files in os.walk(self.root):
            for file in files:
                if not ".MOV" in file:
                    continue
                newFolder = os.path.join(root, "videos")
                toTranscode = os.path.join(root, file)
                
                creationTime = time.strftime('%Y-%m-%d_%H-%M-%S',time.localtime(os.path.getmtime(toTranscode)))
                
                newFile = os.path.join(
                    newFolder,
                    creationTime
                    + "_"
                    + file.replace(".MOV", "_" + self.quality + ".mp4"),
                )
                Path(newFolder).mkdir(exist_ok=True)
                print("Transcode " + toTranscode + " -> " + newFile + " ...")
                self.transcoded[toTranscode] = newFile
                Transcoder(toTranscode, newFile, self.quality)()
                
        print("\n----------------------------------------------------\n")
        for key, value in self.transcoded.items():
            print("Transcoded " + key + " -> " + value)


if __name__ == "__main__":
    args = parser.parse_args()
    path = ""
    if args.input == "NULL":
        path = filedialog.askdirectory()
    else:
        path = args.input

    MovTranscoder(path, args.quality)()
