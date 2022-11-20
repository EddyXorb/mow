from datetime import datetime
from ..modules.image.imagerenamer import *
import shutil
from os.path import join, exists
import os

testfolder = "tests"
tempsrcfolder = "filestorename"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_renamed")
targetDir = join(dst, "subsubfolder")
srcfile = join(src, "subsubfolder", "test3.JPG")
expectedtargetfile = join(targetDir, "2022-07-27@215555_test3.JPG")


def executeRenamingWith(
    writeXMP=False,
    move=True,
    recursive=True,
    maintainFolderStructure=True,
    useCurrentFilename=False,
    replace="",
) -> ImageRenamer:
    renamer = ImageRenamer(
        RenamerInput(
            src=src,
            dst=dst,
            writeXMP=writeXMP,
            move=move,
            verbose=True,
            maintainFolderStructure=maintainFolderStructure,
            recursive=recursive,
            useCurrentFilename=useCurrentFilename,
            replace=replace,
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
        tags = et.get_tags(expectedtargetfile, ["XMP-dc:Source", "XMP-dc:Date"])[0]
        assert tags["XMP:Source"] == "test3.JPG"
        assert tags["XMP:Date"] == "2022:07:27 21:55:55"


def test_alreadyexistentfileisnotoverwritten():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should contain only one file

    renamer = executeRenamingWith(move=False)

    assert len(renamer.toSkip) == 0

    renamer = executeRenamingWith(move=False)

    assert len(renamer.toSkip) == 1


def test_recursiveDisablingWorks():
    prepareTest()

    renamer = executeRenamingWith(move=False, recursive=False)

    assert len(renamer.toTreat) == 0


def test_disableMaintainFolderStructureWorks():
    prepareTest()

    renamer = executeRenamingWith(
        move=False, recursive=True, maintainFolderStructure=False
    )

    assert len(renamer.toTreat) == 1
    assert os.path.exists(join(dst, os.path.basename(expectedtargetfile)))


def test_useFilenameAsSourceOfTruth():
    prepareTest()

    srcfile = join(src, "subsubfolder", "test3.JPG")
    newfile = join(os.path.dirname(srcfile), "2022-11-11@111111_test3.JPG")
    os.rename(srcfile, newfile)

    assert exists(newfile)

    executeRenamingWith(useCurrentFilename=True, writeXMP=True)

    renamedFile = join(targetDir, "2022-11-11@111111_test3.JPG")
    assert exists(renamedFile)

    from exiftool import ExifToolHelper

    with ExifToolHelper() as et:
        tags = et.get_tags(renamedFile, ["XMP-dc:Source", "XMP-dc:Date"])[0]
        assert tags["XMP:Source"] == "2022-11-11@111111_test3.JPG"
        assert tags["XMP:Date"] == "2022:11:11 11:11:11"


def test_replaceWorks():
    prepareTest()

    executeRenamingWith(move=True, replace="test,qwert")

    assert exists(join(src, "subsubfolder", "qwert3.JPG"))


def test_replaceWithRegexWorks():
    prepareTest()

    executeRenamingWith(move=True, replace=r"\d,99")

    assert exists(join(src, "subsubfolder", "test99.JPG"))
