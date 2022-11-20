import shutil
from os.path import join, exists
import os

from ..modules.general.mediarater import MediaRater
from ..modules.general.mediatransitioner import TransitionerInput
from exiftool import ExifToolHelper

import logging

logging.basicConfig(level=logging.DEBUG)

testfolder = "tests"
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_treated")


def prepareTest(srcname):
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcname))
    shutil.copy(
        join(testfolder, "unrated.JPG"),
        join(srcname),
    )


def test_ratedImageIsMoved():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    with ExifToolHelper() as et:
        p = et.set_tags(
            fullname, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False))()

        assert not exists(fullname)
        assert exists(join(dst, groupname, "test.JPG"))


def test_unratedImageIsNotMoved():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False))()

    assert exists(fullname)
    assert not exists(join(dst, groupname, "test.JPG"))
