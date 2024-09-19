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


def test_copiedRatingFromJPGToORF():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    fullnameRaw = join(src, groupname, "test.ORF")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test.ORF"),
        join(fullnameRaw),
    )

    assert exists(fullname)
    assert exists(fullnameRaw)

    with ExifToolHelper() as et:
        p = et.set_tags(
            fullname, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False,writeXMPTags=True))()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        ratingRaw = et.get_tags(join(dst, groupname, "test.ORF"),["XMP:Rating"])[0]
        assert "XMP:Rating" in ratingRaw
        assert ratingRaw["XMP:Rating"] == 3

def test_copiedRatingFromORFToJPG():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    fullnameRaw = join(src, groupname, "test.ORF")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test.ORF"),
        join(fullnameRaw),
    )

    assert exists(fullname)
    assert exists(fullnameRaw)

    with ExifToolHelper() as et:
        p = et.set_tags(
            fullnameRaw, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False,writeXMPTags=True))()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        ratingJPG = et.get_tags(join(dst, groupname, "test.JPG"),["XMP:Rating"])[0]
        assert "XMP:Rating" in ratingJPG
        assert ratingJPG["XMP:Rating"] == 3

def test_differentRatingBetweenJPGandRawpreventsTransition():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    fullnameRaw = join(src, groupname, "test.ORF")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test.ORF"),
        join(fullnameRaw),
    )

    assert exists(fullname)
    assert exists(fullnameRaw)

    with ExifToolHelper() as et:
        et.set_tags(
            fullnameRaw, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )
        et.set_tags(
            fullname, {"XMP:rating": 2}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False,writeXMPTags=True))()

        assert exists(fullname)
        assert exists(fullnameRaw)
        assert not exists(join(dst, groupname, "test.JPG"))
        assert not exists(join(dst, groupname, "test.ORF"))


def test_differentRatingBetweenJPGandRawDoesNotPreventTransitionIfOverrulingFileendingIsSet():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    fullnameRaw = join(src, groupname, "test.ORF")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test.ORF"),
        join(fullnameRaw),
    )

    assert exists(fullname)
    assert exists(fullnameRaw)

    with ExifToolHelper() as et:
        et.set_tags(
            fullnameRaw, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )
        et.set_tags(
            fullname, {"XMP:rating": 2}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False,writeXMPTags=True),overrulingfiletype="JPG")()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        assert et.get_tags(join(dst, groupname, "test.ORF"),"XMP:Rating")[0]["XMP:Rating"] == 2
        assert et.get_tags(join(dst, groupname, "test.JPG"),"XMP:Rating")[0]["XMP:Rating"] == 2

def test_differentRatingBetweenJPGandRawDoesNotPreventTransitionIfOverrulingFileendingIsSetButFileHasNoRating():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    fullnameRaw = join(src, groupname, "test.ORF")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test.ORF"),
        join(fullnameRaw),
    )

    assert exists(fullname)
    assert exists(fullnameRaw)

    with ExifToolHelper() as et:
        et.set_tags(
            fullnameRaw, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )
        et.set_tags(
            fullname, {"XMP:rating": None}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False,writeXMPTags=True),overrulingfiletype="JPG")()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        assert et.get_tags(join(dst, groupname, "test.ORF"),"XMP:Rating")[0]["XMP:Rating"] == 3
        assert et.get_tags(join(dst, groupname, "test.JPG"),"XMP:Rating")[0]["XMP:Rating"] == 3

def test_differentRatingBetweenJPGandRawPreventsTransitionIfOverrulingFileendingIsSetButFileendingNotExistent():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    fullnameRaw = join(src, groupname, "test.ORF")
    prepareTest(srcname=fullname)
    shutil.copy(
        join(testfolder, "test.ORF"),
        join(fullnameRaw),
    )

    assert exists(fullname)
    assert exists(fullnameRaw)

    with ExifToolHelper() as et:
        et.set_tags(
            fullnameRaw, {"XMP:rating": 3}, params=["-P", "-overwrite_original", "-v2"]
        )
        et.set_tags(
            fullname, {"XMP:rating": 2}, params=["-P", "-overwrite_original", "-v2"]
        )

        MediaRater(input=TransitionerInput(src=src, dst=dst, verbose=True, dry=False,writeXMPTags=True),overrulingfiletype="IMAMNOTHERE")()

        assert exists(fullname)
        assert exists(fullnameRaw)
        assert not exists(join(dst, groupname, "test.JPG"))
        assert not exists(join(dst, groupname, "test.ORF"))
