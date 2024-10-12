import sys
import os


def getInputDir(title: str = "open") -> str:
    from tkinter import filedialog
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title=title, initialdir=os.getcwd())
    if folder is None or not os.path.isdir(folder):
        print("No dir specified. Abort.")
        sys.exit()
    return folder


def getInputFile(title: str = "open") -> str:
    from tkinter import filedialog
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(title=title, initialdir=os.getcwd())
    if files is None or not os.path.exists(files[0]):
        print("No file specified. Abort.")
        sys.exit()
    return files[0]
