import shutil
from os.path import join, exists
import os

from ..modules.general.mediagrouper import MediaGrouper, GrouperInput

testfolder = "tests"
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_treated")
imagename = "test3.JPG"
srcfile = join(src, imagename)
expectedConvertedImageFile = join(dst, "subsubfolder", imagename)
from exiftool import ExifToolHelper


def prepareTest(srcname="test.JPG"):
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    print(f"Create dirs {os.path.dirname(srcname)}")
    os.makedirs(os.path.dirname(srcname))
    shutil.copy(
        join(testfolder, "test3.JPG"),
        join(srcname),
    )


def test_correctlyNamedGroupIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=False, verbose=True)
    )()

    assert not exists(fullname)
    assert exists(join(dst, groupname, "test.JPG"))


def test_correctlyNamedGroupIsRecognizedButDryDoesNotMove():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=True, verbose=True)
    )()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.JPG"))


def test_WrongTimestampHoursAreRecognized():
    groupname = "2022-12-12@991212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.JPG"))


def test_TimestampStartingTooLateIsRecognized():
    groupname = "TODO_2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.JPG"))


def test_AtInGroupnameIsRecognized():
    groupname = "2022-12-12@121212_TEST@TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.JPG"))


def test_CorrectSubsubfolderIsRecognized():
    groupname = join("2022-12-12@121212_Supergroup", "2022-12-12@121212_Subgroup")
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=False, verbose=True)
    )()

    assert not exists(fullname)
    assert exists(join(dst, groupname, "test.JPG"))


def test_WrongSupergroupIsRecognized():
    groupname = join("_2022-12-12@121212_Supergroup", "2022-12-12@121212_Subgroup")
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(src=src, dst=dst, interactive=False, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.JPG"))


def test_createdGroupOfUnGrouped():
    fullname = join(src, "2022-12-12@121212_test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            interactive=False,
            dry=False,
            verbose=True,
            groupUngroupedFiles=True,
        )
    )()

    assert exists(join(src, "TODO_2022-12-12@121212", "2022-12-12@121212_test.JPG"))


def test_shouldNotMoveAutomaticallyGroupedFilesIntoDst():
    fullname = join(src, "2022-12-12@121212_test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            interactive=False,
            dry=False,
            verbose=True,
            groupUngroupedFiles=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(dst, "TODO_2022-12-12@121212", "2022-12-12@121212_test.JPG"))


def test_connectsTwoFileIfNotTooDistant():
    fullname = join(src, "2022-12-12@120000_test.JPG")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.JPG"),
        join(src, "2022-12-12@155959_test.JPG"),
    )

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            interactive=False,
            dry=False,
            verbose=True,
            separationDistanceInHours=4,
            groupUngroupedFiles=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(src, "2022-12-12@155959_test.JPG"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.JPG"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@155959_test.JPG"))


def test_connectsTwoFileIfNotTooDistant():
    fullname = join(src, "2022-12-12@120000_test.JPG")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.JPG"),
        join(src, "2022-12-12@160000_test.JPG"),
    )

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            interactive=False,
            dry=False,
            verbose=True,
            separationDistanceInHours=4,
            groupUngroupedFiles=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(src, "2022-12-12@160000_test.JPG"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.JPG"))
    assert exists(join(src, "TODO_2022-12-12@160000", "2022-12-12@160000_test.JPG"))


def test_XMPisWritten():
    fullname = join(src, "2022-12-12@120000 TEST", "2022-12-12@120000_test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            verbose=True,
            writeXMP=True,
        )
    )()

    assert not exists(fullname)
    newname = join(dst, "2022-12-12@120000 TEST", "2022-12-12@120000_test.JPG")
    assert exists(newname)
    with ExifToolHelper() as et:
        tags = et.get_tags(newname, ["XMP-dc:Description"])[0]
        print(tags)
        assert tags["XMP:Description"] == "2022-12-12@120000 TEST"
