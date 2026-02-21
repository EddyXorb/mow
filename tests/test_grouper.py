from pathlib import Path
import shutil
from os.path import join, exists
import os
from exiftool import ExifToolHelper

from modules.mow.mowtags import MowTag

from modules.mow.mowtags import MowTagFileManipulator

from ..modules.general.mediagrouper import MediaGrouper, GrouperInput

testfolder = "tests"
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_treated")
imagename = "test3.jpg"
srcfile = join(src, imagename)
expectedConvertedImageFile = join(dst, "subsubfolder", imagename)


def prepareTest(srcname="test.jpg"):
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcname))
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(srcname),
    )


def test_correctlyNamedGroupIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert not exists(fullname)
    assert exists(join(dst, groupname, "test.jpg"))


def test_GroupWithoutDescriptionIsRejected():
    groupname = "2022-12-12@121212_"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.jpg"))


def test_GroupWithVeryShortDescriptionIsAccepted():
    groupname = "2022-12-12@121212_T"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert not exists(fullname)
    assert exists(join(dst, groupname, "test.jpg"))


def test_correctlyNamedGroupIsRecognizedButDryDoesNotMove():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=True))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.jpg"))


def test_WrongTimestampHoursAreRecognized():
    groupname = "2022-12-12@991212_TEST"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.jpg"))


def test_TimestampStartingTooLateIsRecognized():
    groupname = "TODO_2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.jpg"))


def test_AtInGroupnameIsRecognizedAndWillBeRefused():
    groupname = "2022-12-12@121212_TEST@TEST"
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.jpg"))


def test_CorrectSubsubfolderIsRecognized():
    groupname = join("2022-12-12@121212_Supergroup", "2022-12-12@121212_Subgroup")
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert not exists(fullname)
    assert exists(join(dst, groupname, "test.jpg"))


def test_WrongSupergroupIsRecognized():
    groupname = join("_2022-12-12@121212_Supergroup", "2022-12-12@121212_Subgroup")
    fullname = join(src, groupname, "test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(input=GrouperInput(src=src, dst=dst, dry=False))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.jpg"))


def test_createdGroupOfUnGrouped():
    fullname = join(src, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            automaticGrouping=True,
        )
    )()

    assert exists(join(src, "TODO_2022-12-12@121212", "2022-12-12@121212_test.jpg"))


def test_shouldNotMoveAutomaticallyGroupedFilesIntoDst():
    fullname = join(src, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            automaticGrouping=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(dst, "TODO_2022-12-12@121212", "2022-12-12@121212_test.jpg"))


def test_connectsTwoFileIfNotTooDistant():
    fullname = join(src, "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "2022-12-12@155959_test.jpg"),
    )

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(src, "2022-12-12@155959_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@155959_test.jpg"))


def test_doesNotconnectTwoFileIfTooDistant():
    fullname = join(src, "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "2022-12-12@160000_test.jpg"),
    )

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(src, "2022-12-12@160000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@160000", "2022-12-12@160000_test.jpg"))


def test_intermediateFileProlongsGroup():
    fullname = join(src, "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "2022-12-12@150000_test.jpg"),
    )
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "2022-12-12@180000_test.jpg"),
    )

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(src, "2022-12-12@160000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@150000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@180000_test.jpg"))


def test_XMPisWritten():
    fullname = join(src, "2022-12-12@120000 TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            writeMetaTags=True,
            writeMetaTagsToSidecar=True,
        )
    )()

    assert not exists(fullname)
    newname = Path(dst) / "2022-12-12@120000 TEST" / "2022-12-12@120000_test.jpg"
    assert exists(newname)

    with ExifToolHelper() as et:
        tags = et.get_tags(newname.with_suffix(".xmp"), [MowTag.description.value])[0]
        print(tags)
        assert tags[MowTag.description.value] == "2022-12-12@120000 TEST"


def test_XMPDescriptionContainsAllSuperfolders():
    fullname = join(
        src,
        "2022-12-12@120000 TEST",
        "2022-12-12@120000 TEST2",
        "2022-12-12@120000_test.jpg",
    )
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            writeMetaTags=True,
            writeMetaTagsToSidecar=True,
        )
    )()

    assert not exists(fullname)
    newname = (
        Path(dst)
        / "2022-12-12@120000 TEST"
        / "2022-12-12@120000 TEST2"
        / "2022-12-12@120000_test.jpg"
    )

    assert exists(newname)
    with ExifToolHelper() as et:
        tags = et.get_tags(newname.with_suffix(".xmp"), ["XMP:Description"])[0]
        print(tags)
        assert (
            tags["XMP:Description"] == "2022-12-12@120000 TEST/2022-12-12@120000 TEST2"
        )


def test_groupingMovesJpgAndRAWFiles():
    fullname = join(src, "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "2022-12-12@120000_test.ORF"),
    )
    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
        )
    )()

    assert not exists(fullname)
    assert not exists(join(src, "2022-12-12@120000_test.ORF"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.jpg"))
    assert exists(join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.ORF"))


def test_undoGroupingWorks():
    fullname = join(src, "TODO_2022-12-12@120000", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
            undoAutomatedGrouping=True,
        )
    )()

    assert not exists(fullname)
    assert exists(join(src, "2022-12-12@120000_test.jpg"))


def test_undoGroupingDoesNotTouchGroupsWithoutTODOPrefix():
    fullname = join(src, "2022-12-12@120000", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
            undoAutomatedGrouping=True,
        )
    )()

    assert exists(fullname)
    assert not exists(join(src, "2022-12-12@120000_test.jpg"))


def test_undoGroupingDoesNotTouchTODO_GroupsWithDescription():
    fullname = join(src, "2022-12-12@120000 TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=True,
            undoAutomatedGrouping=True,
        )
    )()

    assert exists(fullname)
    assert not exists(join(src, "2022-12-12@120000_test.jpg"))


def test_addMissingTimestampWorks():
    fullname = join(src, "TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert not exists(fullname)
    assert exists(join(src, "2022-12-12@120000 TEST", "2022-12-12@120000_test.jpg"))


def test_addMissingTimestampWorksRecursively():
    fullname = join(src, "TEST", "TEST2", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert not exists(fullname)
    assert exists(
        join(
            src,
            "2022-12-12@120000 TEST",
            "2022-12-12@120000 TEST2",
            "2022-12-12@120000_test.jpg",
        )
    )


def test_addMissingTimestampTakesLowestDatetime():
    fullname = join(src, "TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "TEST", "2022-12-12@180000_test.jpg"),
    )
    shutil.copy(
        join(testfolder, "test3.jpg"),
        join(src, "TEST", "2022-11-12@180000_test.jpg"),
    )

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert not exists(fullname)
    assert exists(join(src, "2022-11-12@180000 TEST", "2022-12-12@120000_test.jpg"))
    assert exists(join(src, "2022-11-12@180000 TEST", "2022-12-12@180000_test.jpg"))
    assert exists(join(src, "2022-11-12@180000 TEST", "2022-11-12@180000_test.jpg"))


def test_addMissingTimestampWillNotRenameIfDateIsPresent():
    fullname = join(src, "2022-12-12 TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert exists(fullname)
    assert not exists(
        join(src, "2022-12-12@120000 2022-12-12 TEST", "2022-12-12@120000_test.jpg")
    )


def test_addMissingTimestampWillNotRenameIfDateIsSomewhereInTheMiddle():
    fullname = join(src, "TEST2022-12-12TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert exists(fullname)
    assert not exists(
        join(src, "2022-12-12@120000 TEST2022-12-12TEST", "2022-12-12@120000_test.jpg")
    )


def test_addMissingTimestampWillNotRenameIfShortDateIsPresent():
    fullname = join(src, "TEST22-12-12TEST", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert exists(fullname)
    assert not exists(
        join(src, "2022-12-12@120000 TEST22-12-12TEST", "2022-12-12@120000_test.jpg")
    )


def test_addMissingTimestampWillNotRenameIfAtIsPresent():
    fullname = join(src, "TEST@", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert exists(fullname)
    assert not exists(
        join(src, "2022-12-12@120000 TEST@", "2022-12-12@120000_test.jpg")
    )


def test_addMissingTimestampWillWorkIfSomeNumberIsPresent():
    fullname = join(src, "TEST12", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert not exists(fullname)
    assert exists(join(src, "2022-12-12@120000 TEST12", "2022-12-12@120000_test.jpg"))


def test_addMissingTimestampWillWorkIfSomeNumberAndNotDateDashesArePresent():
    fullname = join(src, "TEST122-122-122", "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=True,
        )
    )()

    assert not exists(fullname)
    assert exists(
        join(src, "2022-12-12@120000 TEST122-122-122", "2022-12-12@120000_test.jpg")
    )


def test_groupByXMPdoesWork():
    fullname = join(src, "2022-12-12@120000_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    group = "2022-12-12@120000 Subfolder"
    MowTagFileManipulator().write_tags(
        Path(fullname),
        {MowTag.description: group},
    )

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=False,
            groupByXmp=True,
        )
    )()

    assert not exists(fullname)
    assert exists(join(src, group, "2022-12-12@120000_test.jpg"))


def test_groupByXMPNotExecutedIfAlreadyInGroupSubfolder():
    fullname = join(
        src, "2022-12-12@120000 TEST122-122-122", "2022-12-12@120000_test.jpg"
    )
    prepareTest(srcname=fullname)

    assert exists(fullname)

    group = "2022-12-12@120000 Subfolder"
    MowTagFileManipulator().write_tags(
        Path(fullname),
        {MowTag.description: group},
    )

    MediaGrouper(
        input=GrouperInput(
            src=src,
            dst=dst,
            dry=False,
            separationDistanceInHours=4,
            automaticGrouping=False,
            undoAutomatedGrouping=False,
            addMissingTimestampsToSubfolders=False,
            groupByXmp=True,
        )
    )()

    assert exists(fullname)
    assert not exists(join(src, group, "2022-12-12@120000_test.jpg"))
