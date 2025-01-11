from datetime import datetime
from pathlib import Path

from ..modules.audio.audiorenamer import AudioRenamer
from ..modules.general.mediarenamer import MediaRenamer, RenamerInput
from ..modules.image.imagerenamer import ImageRenamer
import shutil
from os.path import join, exists
import os

testfolder = "tests"
tempsrcfolder = "filestorename"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_renamed")
targetDir = join(dst, "subsubfolder")
srcimagefile = join(src, "subsubfolder", "test3.JPG")
srcaudiofile = join(src, "subsubfolder", "test_audio.mp3")
expectedfilename = "2022-07-27@215555_test3.JPG"
expectedtargetimagefile = Path(targetDir) / expectedfilename

NR_MEDIAFILES = 2


def executeRenamingWith(
    writeMetaTags=False,
    writeMetaTagsToSidecar=True,
    move=True,
    recursive=True,
    maintainFolderStructure=True,
    useCurrentFilename=False,
    replace="",
) -> list[MediaRenamer]:
    def getRenamerInput():
        return RenamerInput(
            src=src,
            dst=dst,
            writeMetaTags=writeMetaTags,
            move=move,
            maintainFolderStructure=maintainFolderStructure,
            recursive=recursive,
            useCurrentFilename=useCurrentFilename,
            replace=replace,
            writeMetaTagsToSidecar=writeMetaTagsToSidecar,
        )

    renamers: list[MediaRenamer] = [
        ImageRenamer(getRenamerInput()),
        AudioRenamer(getRenamerInput()),
    ]
    for r in renamers:
        r()
    return renamers


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcimagefile), exist_ok=True)
    os.makedirs(os.path.dirname(srcaudiofile), exist_ok=True)
    shutil.copy(
        join(testfolder, "test3.JPG"),
        srcimagefile,
    )
    shutil.copy(
        join(testfolder, "test_audio.mp3"),
        srcaudiofile,
    )


def test_subfolderaremaintained():
    prepareTest()

    renamers = executeRenamingWith()
    assert len(renamers[0].toTreat) == 1

    assert not exists(srcimagefile)
    assert not exists(srcaudiofile)

    assert exists(expectedtargetimagefile)
    assert len(list(filter(lambda x: ".mp3" in x, os.listdir(targetDir)))) == 1


def test_copyworks():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == NR_MEDIAFILES
    )  # source should contain only one file

    executeRenamingWith(move=False)

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == NR_MEDIAFILES
    )  # source should still contain only one file
    assert (
        len(os.listdir(targetDir)) == NR_MEDIAFILES
    )  # should contain a new file after copying


def test_moveworks():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == NR_MEDIAFILES
    )  # source should contain only one file

    executeRenamingWith(move=True)

    assert (
        len(os.listdir(os.path.dirname(srcimagefile))) == 0
    )  # source should still contain only one file
    assert (
        len(os.listdir(targetDir)) == NR_MEDIAFILES
    )  # should contain a new file after copying


def test_nonemptyDestinationIsNoProblem():
    prepareTest()
    os.makedirs(dst, exist_ok=True)

    executeRenamingWith()

    assert (
        len(os.listdir(targetDir)) == NR_MEDIAFILES
    )  # should contain a new file after copying


def test_timeStampIsCorrect():
    prepareTest()

    renamers = executeRenamingWith()

    for renamer in renamers:
        for task in renamer.getFinishedTasks():
            timestamp = task.newName.split("_")[
                0
            ]  # we assume YYYY-MM-DD@HHMMSS_OLDNAME e.g. "2022-07-27@215555_test3"
            assert len(timestamp) == 17
            _ = datetime.strptime(timestamp, "%Y-%m-%d@%H%M%S")


def test_writeXMPDateAndCreationWorks():
    prepareTest()

    executeRenamingWith(writeMetaTags=True)
    from exiftool import ExifToolHelper

    with ExifToolHelper() as et:
        tags = et.get_tags(
            str(expectedtargetimagefile.with_suffix(".xmp")), ["XMP:Source", "XMP:Date"]
        )[0]
        assert tags["XMP:Source"] == "test3.JPG"
        assert tags["XMP:Date"] == "2022:07:27 21:55:55"


def test_alreadyexistentfileisnotoverwritten():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == NR_MEDIAFILES
    )  # source should contain only one file

    renamers = executeRenamingWith(move=False)

    for renamer in renamers:
        assert len(renamer.getSkippedTasks()) == 0

    renamers = executeRenamingWith(move=False)

    for renamer in renamers:
        assert len(renamer.getSkippedTasks()) == 1


def test_recursiveDisablingWorks():
    prepareTest()

    renamers = executeRenamingWith(move=False, recursive=False)

    for renamer in renamers:
        assert len(renamer.toTreat) == 0


def test_disableMaintainFolderStructureWorks():
    prepareTest()

    renamers = executeRenamingWith(
        move=False, recursive=True, maintainFolderStructure=False
    )

    for renamer in renamers:
        assert len(renamer.toTreat) == 1

    assert len(os.listdir(dst)) == NR_MEDIAFILES


def test_useFilenameAsSourceOfTruth():
    prepareTest()

    srcfile = join(src, "subsubfolder", "test3.JPG")
    newfile = join(os.path.dirname(srcfile), "2022-11-11@111111_test3.JPG")
    os.rename(srcfile, newfile)

    assert exists(newfile)

    executeRenamingWith(useCurrentFilename=True, writeMetaTags=True)

    renamedFile = Path(targetDir) / "2022-11-11@111111_test3.JPG"
    assert exists(renamedFile)

    from exiftool import ExifToolHelper

    with ExifToolHelper() as et:
        tags = et.get_tags(renamedFile.with_suffix(".xmp"), ["XMP:Source", "XMP:Date"])[
            0
        ]
        assert tags["XMP:Source"] == "2022-11-11@111111_test3.JPG"
        assert tags["XMP:Date"] == "2022:11:11 11:11:11"


def test_replaceWorks():
    prepareTest()

    executeRenamingWith(move=True, replace="test,qwert")

    assert not exists(srcimagefile)
    assert exists(join(src, "subsubfolder", "qwert3.JPG"))


def test_replaceWithRegexWorks():
    prepareTest()

    renamers = executeRenamingWith(move=True, replace=r"\d,99")
    print(renamers[0].getFinishedTasks())

    assert exists(join(src, "subsubfolder", "test99.JPG"))
