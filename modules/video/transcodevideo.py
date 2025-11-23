import platform
from subprocess import check_output, run, PIPE
import argparse
import os
import subprocess

parser = argparse.ArgumentParser("Videotranscoder")

parser.add_argument("-i", "--input", type=str)

parser.add_argument(
    "-o",
    "--output",
    type=str,
)

parser.add_argument("-q", "--quality", type=str, choices=["hd", "sd", "android"])


class Transcoder:
    """
    quality: preset (one of 'hd','sd')
    qualityvalue: lower values are higher quality, but this is only comparable between the same presets (e.g. the quality-setting)
    """

    def __init__(
        self, input: str, output: str, quality: str, qualityvalue: float = 22.0
    ):
        self.inputFile = input
        self.outputFile = output
        self.quality = quality
        self.containerformatoption = ["--format", "av_mp4"]
        self.sharpoption = ["--lapsharp", "medium"]
        self.presets = {
            "sd": '"H.265 MKV 720p30"',
            "hd": '"H.265 MKV 2160p60 4K"',
            "android": '"Android 720p30"',
        }
        self.qualityValue = ["-q", str(qualityvalue)]

        if self.inputFile is None or self.inputFile == "":
            print("Choose file..", flush=True)
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            self.inputFile = filedialog.askopenfilename()
            self.quality = "hd"
            self.outputFile = os.path.splitext(self.inputFile)[0] + "_converted.mp4"
            print("Set outputfile to " + self.outputFile + "...")

    def getEncoderPreset(self, arg) -> list[str]:
        return [" --preset  " ,self.presets[arg]]

    def getCommand(self) -> str|list[str]:
        handbrake_exe = "HandBrakeCLI.exe" if platform.system() == "Windows" else "HandBrakeCLI"

        command = [handbrake_exe, "-i", self.inputFile, "-o", self.outputFile]

        command += self.getEncoderPreset(self.quality)
        command += self.containerformatoption
        command += self.sharpoption
        command += self.qualityValue

        return command

    def __call__(self):
        cmd = self.getCommand()
        print(f"Call Handbrake with these arguments: {cmd}")
        try:
            out = check_output(cmd, stderr=subprocess.STDOUT)
            print("Transcoding finished. Output:")
            print(out.decode("utf-8"))
            return out
        except subprocess.CalledProcessError as e:
            print("Error during transcoding:")
            print(e.output.decode("utf-8"))
            return None

if __name__ == "__main__":
    args = parser.parse_args()
    Transcoder(args.input, args.output, args.quality)()
