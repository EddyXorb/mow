from datetime import datetime
from ..modules.image.imagerenamer import *
from ..modules.mow.mow import Mow
import shutil
from os.path import *
import os

testfolder = "tests"
workingdir = abspath(join(testfolder, "mow_test_workingdir"))
archivedir = join(workingdir, "7_archive")
aggregatedir = join(workingdir, "6_aggregate")
localizedir = join(workingdir, "5.3_localize")
tagdir = join(workingdir, "5.2_tag")
ratedir = join(workingdir, "5.1_rate")
groupdir = join(workingdir, "4_group")
convertdir = join(workingdir, "3_convert")
renamedir = join(workingdir, "2_rename")
expectedtargetsrcfile = join(convertdir, "subfolder", "2022-07-27@215555_test3.JPG")
settingsfile = ".mow_test_settings.yml"


def prepareTest(targetdir, untouchedfile, starttransitionfile):
    shutil.rmtree(targetdir, ignore_errors=True)
    os.makedirs(dirname(starttransitionfile), exist_ok=True)
    shutil.copy(untouchedfile, starttransitionfile)


def prepareRenameTest():
    prepareTest(
        targetdir=join(workingdir, "3_convert", "subfolder"),
        untouchedfile=join(testfolder, "test3.JPG"),
        starttransitionfile=join(workingdir, "2_rename", "subfolder", "test3.JPG"),
    )


def prepareImageConversionTest():
    prepareTest(
        targetdir=join(workingdir, "4_group", "subfolder"),
        untouchedfile=join(testfolder, "test3.JPG"),
        starttransitionfile=join(workingdir, "3_convert", "subfolder", "test3.JPG"),
    )


def prepareVideoConversionTest():
    prepareTest(
        targetdir=join(workingdir, "4_group", "subfolder"),
        untouchedfile=join(testfolder, "test.MOV"),
        starttransitionfile=join(workingdir, "3_convert", "subfolder", "test.MOV"),
    )


def prepareGroupingTest():
    prepareTest(
        targetdir=join(workingdir, "5.1_rate", "2022-12-12@121212 TEST"),
        untouchedfile=join(testfolder, "test3.JPG"),
        starttransitionfile=join(
            workingdir,
            "4_group",
            "2022-12-12@121212 TEST",
            "2022-12-12@121212_test3.JPG",
        ),
    )


def prepareRateTransitionTest():
    prepareTest(
        targetdir=join(tagdir, "subfolder"),
        untouchedfile=join(testfolder, "rated.jpg"),
        starttransitionfile=join(ratedir, "subfolder", "rated.jpg"),
    )


def prepareTagTransitionTest():
    prepareTest(
        targetdir=join(localizedir, "subfolder"),
        untouchedfile=join(testfolder, "test3.jpg"),
        starttransitionfile=join(tagdir, "subfolder", "tagged.jpg"),
    )


def prepareLocalizeTransitionTest():
    prepareTest(
        targetdir=join(aggregatedir, "subfolder"),
        untouchedfile=join(testfolder, "test3.jpg"),
        starttransitionfile=join(localizedir, "subfolder", "localized.jpg"),
    )


def prepareAggregateTransitionTest(filename: str, groupname: str):
    prepareTest(
        targetdir=join(archivedir, groupname),
        untouchedfile=join(testfolder, "2022-12-12@121212_FINISHED.JPG"),
        starttransitionfile=join(aggregatedir, groupname, filename),
    )


def test_filewasmoved():
    prepareRenameTest()

    srcfile = join(workingdir, "2_rename", "subfolder", "test3.JPG")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).rename(dry=False)
    assert not exists(srcfile)
    assert exists(join(convertdir, "subfolder", "2022-07-27@215555_test3.JPG"))


def test_groupingMovesDirectoriesIntoRateFolder():
    prepareGroupingTest()

    srcfile = join(
        workingdir, "4_group", "2022-12-12@121212 TEST", "2022-12-12@121212_test3.JPG"
    )

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).group(automate=False, distance=12, dry=False)

    assert not exists(srcfile)
    assert exists(
        join(ratedir, "2022-12-12@121212 TEST", "2022-12-12@121212_test3.JPG")
    )


def test_emptyDirsAreremovedInRenameFolder():
    prepareRenameTest()

    assert exists(join(renamedir, "subfolder"))
    Mow(settingsfile=settingsfile).rename(dry=False)
    assert not exists(join(renamedir, "subfolder"))


def test_conversionOfImageWorks():
    prepareImageConversionTest()
    srcfile = join(workingdir, "3_convert", "subfolder", "test3.JPG")
    assert exists(srcfile)

    Mow(settingsfile=settingsfile).convert(dry=False)

    assert not exists(srcfile)
    assert exists(join(workingdir, "4_group", "subfolder", "test3.JPG"))


def test_conversionOfVideoWorks():
    prepareVideoConversionTest()
    srcfile = join(workingdir, "3_convert", "subfolder", "test.MOV")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).convert(dry=False)

    assert not exists(srcfile)
    assert exists(join(workingdir, "4_group", "subfolder", "test_original.MOV"))
    assert exists(join(workingdir, "4_group", "subfolder", "test.mp4"))


def test_ratedImageIsTransitioned():
    prepareRateTransitionTest()
    srcfile = join(ratedir, "subfolder", "rated.jpg")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).rate(dry=False)

    assert not exists(srcfile)
    assert exists(join(tagdir, "subfolder", "rated.jpg"))


def test_taggedImageIsTransitioned():
    prepareTagTransitionTest()
    srcfile = join(tagdir, "subfolder", "tagged.jpg")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).tag(dry=False)

    assert not exists(srcfile)
    assert exists(join(localizedir, "subfolder", "tagged.jpg"))


def test_localizedImageIsTransitioned():
    prepareLocalizeTransitionTest()
    srcfile = join(localizedir, "subfolder", "localized.jpg")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).localize(dry=False)

    assert not exists(srcfile)
    assert exists(join(aggregatedir, "subfolder", "localized.jpg"))


def test_aggregatableImageIsTransitioned():
    group = "2022-12-12@121212_TEST"
    file = "2022-12-12@121212_aggregated.jpg"
    prepareAggregateTransitionTest(groupname=group, filename=file)
    srcfile = join(aggregatedir, group, file)

    assert exists(srcfile)

    Mow(settingsfile=settingsfile).aggregate(dry=False)

    assert not exists(srcfile)
    assert exists(join(archivedir, group, file))
