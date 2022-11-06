from datetime import datetime

from ..modules.video.videorenamer import VideoRenamer
from ..modules.image.imagerenamer import *
import shutil
from os.path import join, exists
import os

testfolder = "tests"
tempsrcfolder = "filestorename"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_renamed")
targetDir = join(dst, "subsubfolder")
srcfile = join(src, "subsubfolder", "test.MOV")


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join(testfolder, "test.MOV"),
        srcfile,
    )


def test_fileisrenamed():
    prepareTest()

    renamer = VideoRenamer(src, dst, move=True, verbose=True)
    renamer()
    assert len(os.listdir(targetDir)) > 0
