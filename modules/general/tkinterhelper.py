import sys
import os


def getInputDir(title: str = "open") -> str:
    from tkinter import filedialog
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title=title, initialdir=os.getcwd())
    if not os.path.isdir(folder):
        print("No dir specified, do nothing.")
        sys.exit()
    return folder
