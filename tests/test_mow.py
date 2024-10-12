from pathlib import Path

from ..modules.general.mediatransitioner import DELETE_FOLDER_NAME
from ..modules.general.medialocalizer import BaseLocalizerInput
from ..modules.mow.mowtags import MowTags
from ..modules.image.imagerenamer import *
from ..modules.mow.mow import Mow
import shutil
from os.path import *
import os
from exiftool import ExifToolHelper

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
    shutil.rmtree(Path(convertdir) / DELETE_FOLDER_NAME, ignore_errors=True)
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
    shutil.rmtree(Path(localizedir) / "subfolder", ignore_errors=True)
    prepareTest(
        targetdir=join(aggregatedir, "subfolder"),
        untouchedfile=join(testfolder, "test3.jpg"),
        starttransitionfile=join(
            localizedir, "subfolder", "2024-12-12@121212_TEST.jpg"
        ),
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

    Mow(settingsfile=settingsfile, dry=False).rename()
    assert not exists(srcfile)
    assert exists(join(convertdir, "subfolder", "2022-07-27@215555_test3.JPG"))


def test_stage_history_was_added():
    prepareImageConversionTest()
    prepareRenameTest()

    srcfile = join(workingdir, "2_rename", "subfolder", "test3.JPG")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).rename()
    assert not exists(srcfile)
    target_file_renaming = join(convertdir, "subfolder", "2022-07-27@215555_test3.JPG")
    assert exists(target_file_renaming)

    with ExifToolHelper() as et:
        tags = et.get_tags(
            target_file_renaming, ["XMP:Contributor"], params=["-struct"]
        )[0]
        assert MowTags.stagehistory in tags
        assert os.path.basename(renamedir) in tags[MowTags.stagehistory]

    Mow(settingsfile=settingsfile, dry=False).convert()

    assert not exists(target_file_renaming)
    target_file_conversion = join(
        workingdir, "4_group", "subfolder", "2022-07-27@215555_test3.JPG"
    )
    assert exists(target_file_conversion)

    with ExifToolHelper() as et:
        tags = et.get_tags(
            target_file_conversion, ["XMP:Contributor"], params=["-struct"]
        )[0]
        print(tags)
        assert MowTags.stagehistory in tags
        assert os.path.basename(convertdir) in tags[MowTags.stagehistory]


def test_groupingMovesDirectoriesIntoRateFolder():
    prepareGroupingTest()

    srcfile = join(
        workingdir, "4_group", "2022-12-12@121212 TEST", "2022-12-12@121212_test3.JPG"
    )

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).group(automate=False, distance=12)

    assert not exists(srcfile)
    assert exists(
        join(ratedir, "2022-12-12@121212 TEST", "2022-12-12@121212_test3.JPG")
    )


def test_emptyDirsAreremovedInRenameFolder():
    prepareRenameTest()

    assert exists(join(renamedir, "subfolder"))
    Mow(settingsfile=settingsfile, dry=False).rename()
    assert not exists(join(renamedir, "subfolder"))


def test_conversionOfImageWorks():
    prepareImageConversionTest()
    srcfile = join(workingdir, "3_convert", "subfolder", "test3.JPG")
    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).convert()

    assert not exists(srcfile)
    assert exists(join(workingdir, "4_group", "subfolder", "test3.JPG"))


def test_conversionOfVideoWorks():
    prepareVideoConversionTest()
    srcfile = join(workingdir, "3_convert", "subfolder", "test.MOV")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).convert()

    assert not exists(srcfile)
    assert exists(join(workingdir, "3_convert", DELETE_FOLDER_NAME, "subfolder", "test.MOV"))
    assert exists(join(workingdir, "4_group", "subfolder", "test.mp4"))


def test_conversionOfPassthroughVideoWorks():
    prepareVideoConversionTest()
    srcfile = join(workingdir, "3_convert", "subfolder", "test.MOV")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).convert(enforcePassthrough=True)

    assert not exists(srcfile)
    assert not exists(join(workingdir, "3_convert", DELETE_FOLDER_NAME, "subfolder", "test.MOV"))
    assert exists(join(workingdir, "4_group", "subfolder", "test.MOV"))


def test_ratedImageIsTransitioned():
    prepareRateTransitionTest()
    srcfile = join(ratedir, "subfolder", "rated.jpg")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).rate()

    assert not exists(srcfile)
    assert exists(join(tagdir, "subfolder", "rated.jpg"))


def test_taggedImageIsTransitioned():
    prepareTagTransitionTest()
    srcfile = join(tagdir, "subfolder", "tagged.jpg")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).tag()

    assert not exists(srcfile)
    assert exists(join(localizedir, "subfolder", "tagged.jpg"))


def test_localizedImageIsTransitioned():
    prepareLocalizeTransitionTest()
    srcfile = join(localizedir, "subfolder", "2024-12-12@121212_TEST.jpg")

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).localize(
        localizerInput=BaseLocalizerInput(transition_even_if_no_gps_data=True)
    )

    assert not exists(srcfile)
    assert exists(join(aggregatedir, "subfolder", "2024-12-12@121212_TEST.jpg"))


def test_aggregatableImageIsTransitioned():
    group = "2022-12-12@121212_TEST"
    file = "2022-12-12@121212_aggregated.jpg"
    prepareAggregateTransitionTest(groupname=group, filename=file)
    srcfile = join(aggregatedir, group, file)

    assert exists(srcfile)

    Mow(settingsfile=settingsfile, dry=False).aggregate(jpgIsSingleSourceOfTruth=False)

    assert not exists(srcfile)
    assert exists(join(archivedir, group, file))


def test_filteringfiles_passes():
    prepareLocalizeTransitionTest()
    srcfile = join(localizedir, "subfolder", "2024-12-12@121212_TEST.jpg")

    assert exists(srcfile)

    Mow(
        settingsfile=settingsfile, dry=False, filter="2024-12-12@121212_TES.*"
    ).localize(BaseLocalizerInput(transition_even_if_no_gps_data=True))

    assert not exists(srcfile)
    assert exists(join(aggregatedir, "subfolder", "2024-12-12@121212_TEST.jpg"))


def test_filteringfiles_blocks():
    prepareLocalizeTransitionTest()
    srcfile = join(localizedir, "subfolder", "2024-12-12@121212_TEST.jpg")

    assert exists(srcfile)

    Mow(
        settingsfile=settingsfile, dry=False, filter="THERE_IS_NO_FILE_WITH_THIS_NAME"
    ).localize(BaseLocalizerInput(transition_even_if_no_gps_data=True))

    assert exists(srcfile)
    assert not exists(join(aggregatedir, "subfolder", "2024-12-12@121212_TEST.jpg"))
