import hashlib
import io
from tqdm import tqdm
import os
import tkinter as tk
from tkinter import filedialog
import csv
import argparse

parser = argparse.ArgumentParser("Hasher")
parser.add_argument(
    "-i",
    "--input",
    help="specify inputdir. All files therein will be recursively hashed and the result is saved in same directory in a csv table.",
    type=str,
)


def calcMD5sum(src: str, stepsize=io.DEFAULT_BUFFER_SIZE) -> str:
    calculated = 0
    filesizeMB = os.path.getsize(src) / 1024.0 * 1024.0
    expectedsteps = int(filesizeMB / (stepsize / 1024.0 * 1024.0))
    md5 = hashlib.md5()
    with io.open(src, mode="rb") as fd:
        for chunk in tqdm(
            iter(lambda: fd.read(stepsize), b""),
            unit=str(stepsize),
            total=expectedsteps,
        ):
            md5.update(chunk)
            calculated += len(chunk)
    return md5.hexdigest()


class MD5Hasher:
    def __init__(self, dir: str):
        self.dir = dir
        self.hashfilename = os.path.join(dir, os.path.basename(dir) + "_MD5.csv")
        self.prepareHashResultFile()

    def prepareHashResultFile(self):
        if os.path.exists(self.hashfilename):
            os.remove(self.hashfilename)
        with open(self.hashfilename, "a", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["hash", "file", "dir"])

    def hashFile(self, fullpath: str):
        hash = calcMD5sum(fullpath, 1024 * 1024)
        with open(self.hashfilename, "a", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                [hash, os.path.basename(fullpath), os.path.dirname(fullpath)]
            )

    def __call__(self):
        print("\nWrite hashes to ", self.hashfilename, "\n")

        for root, _, files in os.walk(self.dir):
            for file in files:
                fullpath = os.path.join(root, file)
                self.hashFile(fullpath)


if __name__ == "__main__":
    args = parser.parse_args()
    path = ""
    if args.input is None:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory()
    else:
        path = args.input

    print("Hash files in " + path)

    MD5Hasher(os.path.abspath(path))()
