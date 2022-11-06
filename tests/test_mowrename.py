from datetime import datetime
from ..modules.image.imagerenamer import *
from ..modules.mow.mow import Mow
import shutil
from os.path import *

testfolder = "tests"
workingdir = abspath(join(testfolder, "mow_test_workingdir"))
convertdir = join(workingdir, "3_convert")
renamedir = join(workingdir, "2_rename")
targetdir = join(convertdir, "subfolder")
srcfile = join(renamedir, "subfolder", "test3.JPG")
expectedtargetsrcfile = join(convertdir, "subfolder", "2022-07-27@215555_test3.JPG")
settingsfile = ".mow_test_settings.yml"


def prepareTest():
    shutil.rmtree(targetdir, ignore_errors=True)
    os.makedirs(dirname(srcfile), exist_ok=True)
    shutil.copy(join(testfolder, "test3.JPG"), srcfile)


def test_filewasmoved():
    prepareTest()
    assert exists(srcfile)
    Mow(settingsfile=settingsfile).rename()
    assert not exists(srcfile)
    assert exists(expectedtargetsrcfile)
