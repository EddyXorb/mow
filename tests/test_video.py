from pathlib import Path
from exiftool import ExifToolHelper


from ..modules.mow.mowtags import MowTag, tags_all

from ..modules.general.mediatransitioner import DELETE_FOLDER_NAME, TransitionerInput
from ..modules.video.videorenamer import VideoRenamer
from ..modules.image.imagerenamer import RenamerInput
from ..modules.video.videoconverter import VideoConverter

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
        RenamerInput(
            src=src,
            dst=dst,
            move=True,
            writeMetaTags=True,
            writeMetaTagsToSidecar=False,
        )
    )
    renamer()
    assert len(os.listdir(targetDir)) > 0


def test_conversionMovesOriginalsIntoDeletedAndCreatesConverted():
    prepareTest()

    assert exists(srcfile)

    VideoConverter(
        TransitionerInput(
            src=src,
            dst=dst,
        )
    )()

    assert not exists(srcfile)
    assert exists(join(targetDir, "test.mp4"))
    assert exists(join(Path(src) / DELETE_FOLDER_NAME / "subsubfolder" / "test.MOV"))


def test_conversionPreservesXMPTags():
    prepareTest()

    assert exists(srcfile)

    tagsDict = {
        tag: "DUMMY_VALUE"
        for tag in [tag.value for tag in tags_all]
        if "Rating" not in tag and "Date" not in tag
    }
    tagsDict["XMP:Rating"] = 2
    tagsDict["XMP:Date"] = "2022:07:27 21:55:55"

    with ExifToolHelper() as et:
        et.set_tags(srcfile, tagsDict)

    VideoConverter(
        TransitionerInput(
            src=src,
            dst=dst,
        )
    )()

    convertedFile = join(targetDir, "test.mp4")

    assert not exists(srcfile)
    assert exists(convertedFile)
    assert exists(join(Path(src) / DELETE_FOLDER_NAME / "subsubfolder" / "test.MOV"))

    with ExifToolHelper() as et:
        tags = et.get_tags(convertedFile, [tag.value for tag in tags_all])[0]

    for tag in [tag.value for tag in tags_all]:
        if "XMP" not in tag:
            continue
        assert tag in tags
