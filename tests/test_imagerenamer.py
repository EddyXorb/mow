from datetime import datetime
from ..modules.image.imagerenamer import *
import shutil
from os.path import join
import os

testfolder = "tests"
tempsrcfolder = "filestorename"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_renamed")
targetDir = join(dst, "subsubfolder")
srcfile = join(src, "subsubfolder", "test3.JPG")
expectedtargetfile = join(targetDir, "2022-07-27@215555_test3.JPG")


def executeRenamingWith(writeXMP=False, move=True) -> ImageRenamer:
    renamer = ImageRenamer(
        RenamerInput(
            src=src,
            dst=dst,
            writeXMP=writeXMP,
            move=move,
            verbose=True,
            maintainFolderStrucuture=True,
        )
    )
    renamer()
    return renamer


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join(testfolder, "test3.JPG"),
        srcfile,
    )


def test_subfolderaremaintained():
    prepareTest()

    renamer = executeRenamingWith()

    assert len(renamer.toTreat) == 1
    for old, new in renamer.oldToNewMapping.items():
        assert os.path.dirname(srcfile) in old
        assert join(testfolder, "test_renamed", "subsubfolder") in new


def test_copyworks():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should contain only one file

    executeRenamingWith(move=False)

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should still contain only one file
    assert len(os.listdir(targetDir)) == 1  # should contain a new file after copying


def test_moveworks():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should contain only one file

    executeRenamingWith(move=True)

    assert (
        len(os.listdir(os.path.dirname(srcfile))) == 0
    )  # source should still contain only one file
    assert len(os.listdir(targetDir)) == 1  # should contain a new file after copying


def test_nonemptyDestinationIsNoProblem():
    prepareTest()
    os.makedirs(dst, exist_ok=True)

    executeRenamingWith()

    assert len(os.listdir(targetDir)) == 1  # should contain a new file after copying


def test_timeStampIsCorrect():
    prepareTest()

    renamer = executeRenamingWith()

    for _, new in renamer.oldToNewMapping.items():
        timestamp = os.path.basename(new).split("_")[
            0
        ]  # we assume YYYY-MM-DD@HHMMSS_OLDNAME e.g. "2022-07-27@215555_test3"
        assert len(timestamp) == 17
        dt = datetime.strptime(timestamp, "%Y-%m-%d@%H%M%S")


def test_writeXMPDateAndCreationWorks():
    prepareTest()

    executeRenamingWith(writeXMP=True)
    from exiftool import ExifToolHelper

    with ExifToolHelper() as et:
        tags = et.get_tags(expectedtargetfile, ["XMP-dc:Source", "XMP-dc:date"])[0]
        assert tags["XMP:Source"] == "test3.JPG"
        assert tags["XMP:Date"] == "2022:07:27 21:55:55"


def test_alreadyexistentfileisnotoverwritten():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should contain only one file

    renamer = executeRenamingWith(move=False)

    assert len(renamer.skippedFiles) == 0

    renamer = executeRenamingWith(move=False)

    assert len(renamer.skippedFiles) == 1