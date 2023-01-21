from exiftool import ExifToolHelper

from ..modules.mow.mowtags import MowTags

from ..modules.video.videorenamer import VideoRenamer
from ..modules.image.imagerenamer import *
from ..modules.video.videoconverter import VideoConverter
from ..modules.general.mediaconverter import ConverterInput

import shutil
from os.path import join, exists
import os

testfolder = "tests"
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_treated")
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

    renamer = VideoRenamer(
        RenamerInput(src=src, dst=dst, move=True, verbose=True, writeXMPTags=True)
    )
    renamer()
    assert len(os.listdir(targetDir)) > 0


def test_passthroughWorks():
    prepareTest()

    assert exists(srcfile)

    VideoConverter(
        ConverterInput(
            src=src,
            dst=dst,
            deleteOriginals=False,
            verbose=True,
            enforcePassthrough=True,
        )
    )()

    assert not exists(srcfile)
    assert not exists(join(targetDir, "test.mp4"))
    assert not exists(join(targetDir, "test_original.MOV"))
    assert exists(join(targetDir, "test.MOV"))


def test_conversionMovesOriginalsAndCreatesConverted():
    prepareTest()

    assert exists(srcfile)

    VideoConverter(
        ConverterInput(
            src=src,
            dst=dst,
            deleteOriginals=False,
            verbose=True,
            enforcePassthrough=False,
        )
    )()

    assert not exists(srcfile)
    assert exists(join(targetDir, "test.mp4"))
    assert exists(join(targetDir, "test_original.MOV"))


def test_conversionDeletesOriginalsIfWanted():
    prepareTest()

    assert exists(srcfile)
    converter = VideoConverter(
        ConverterInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            verbose=True,
            enforcePassthrough=False,
        )
    )
    converter()

    assert not exists(srcfile)
    assert exists(join(targetDir, "test.mp4"))
    assert not exists(join(targetDir, "test_original.MOV"))
    assert exists(join(src, "deleted", "test_original.MOV"))


def test_simpleConversionWorks():
    prepareTest()

    assert exists(srcfile)
    VideoConverter(
        ConverterInput(
            src=src,
            dst=dst,
            deleteOriginals=False,
            verbose=True,
            enforcePassthrough=False,
        )
    )()

    assert not exists(srcfile)
    assert exists(join(targetDir, "test.mp4"))
    assert exists(join(targetDir, "test_original.MOV"))


def test_conversionPreservesXMPTags():
    prepareTest()

    assert exists(srcfile)

    tagsDict = {tag: "DUMMY_VALUE"  for tag in MowTags.all if "Rating" not in tag and "Date" not in tag}
    tagsDict["XMP:Rating"] = 2
    tagsDict["XMP:Date"] = "2022:07:27 21:55:55"
    
    with ExifToolHelper() as et:
        et.set_tags(srcfile, tagsDict)

    VideoConverter(
        ConverterInput(
            src=src,
            dst=dst,
            deleteOriginals=False,
            verbose=True,
            enforcePassthrough=False,
        )
    )()

    convertedFile = join(targetDir, "test.mp4")
    assert not exists(srcfile)
    assert exists(convertedFile)
    assert exists(join(targetDir, "test_original.MOV"))

    with ExifToolHelper() as et:
        tags = et.get_tags(convertedFile, MowTags.all)[0]

    for tag in MowTags.all:
        assert tag in tags
