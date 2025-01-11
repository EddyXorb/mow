import shutil
from os.path import join, exists
import os

from modules.mow.mowtags import MowTag

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
        _ = et.set_tags(
            fullname,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src, dst=dst, dry=False, writeMetaTagsToSidecar=True
            )
        )()

        assert not exists(fullname)
        assert exists(join(dst, groupname, "test.JPG"))


def test_unratedImageIsNotMoved():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaRater(input=TransitionerInput(src=src, dst=dst, dry=False))()

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
        _ = et.set_tags(
            fullname,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                dry=False,
                writeMetaTags=True,
                writeMetaTagsToSidecar=True,
            )
        )()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        ratingRaw = et.get_tags(
            join(dst, groupname, "test.xmp"), [MowTag.rating.value]
        )[0]
        assert MowTag.rating.value in ratingRaw
        assert ratingRaw[MowTag.rating.value] == 3


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
        _ = et.set_tags(
            fullnameRaw,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                dry=False,
                writeMetaTags=True,
                writeMetaTagsToSidecar=True,
            )
        )()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        ratingJPG = et.get_tags(
            join(dst, groupname, "test.xmp"), [MowTag.rating.value]
        )[0]
        assert MowTag.rating.value in ratingJPG
        assert ratingJPG[MowTag.rating.value] == 3


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
            fullnameRaw,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )
        et.set_tags(
            fullname,
            {MowTag.rating.value: 2},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                dry=False,
                writeMetaTags=True,
                writeMetaTagsToSidecar=True,
            )
        )()

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
            fullnameRaw,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )
        et.set_tags(
            fullname,
            {MowTag.rating.value: 2},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                dry=False,
                writeMetaTags=True,
                writeMetaTagsToSidecar=False,
            ),
            overrulingfiletype="JPG",
        )()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        assert (
            et.get_tags(join(dst, groupname, "test.ORF"), MowTag.rating.value)[0][
                MowTag.rating.value
            ]
            == 2
        )
        assert (
            et.get_tags(join(dst, groupname, "test.JPG"), MowTag.rating.value)[0][
                MowTag.rating.value
            ]
            == 2
        )


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
            fullnameRaw,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )
        et.set_tags(
            fullname,
            {MowTag.rating.value: None},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                dry=False,
                writeMetaTags=True,
                writeMetaTagsToSidecar=False,
            ),
            overrulingfiletype="JPG",
        )()

        assert not exists(fullname)
        assert not exists(fullnameRaw)
        assert exists(join(dst, groupname, "test.JPG"))
        assert exists(join(dst, groupname, "test.ORF"))

        assert (
            et.get_tags(join(dst, groupname, "test.ORF"), MowTag.rating.value)[0][
                MowTag.rating.value
            ]
            == 3
        )
        assert (
            et.get_tags(join(dst, groupname, "test.JPG"), MowTag.rating.value)[0][
                MowTag.rating.value
            ]
            == 3
        )


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
            fullnameRaw,
            {MowTag.rating.value: 3},
            params=["-P", "-overwrite_original", "-v2"],
        )
        et.set_tags(
            fullname,
            {MowTag.rating.value: 2},
            params=["-P", "-overwrite_original", "-v2"],
        )

        MediaRater(
            input=TransitionerInput(
                src=src,
                dst=dst,
                dry=False,
                writeMetaTags=True,
                writeMetaTagsToSidecar=False,
            ),
            overrulingfiletype="IMAMNOTHERE",
        )()

        assert exists(fullname)
        assert exists(fullnameRaw)
        assert not exists(join(dst, groupname, "test.JPG"))
        assert not exists(join(dst, groupname, "test.ORF"))


def test_enforced_rating_works():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "test.JPG")
    prepareTest(srcname=fullname)

    assert exists(fullname)

    MediaRater(
        input=TransitionerInput(
            src=src,
            dst=dst,
            dry=False,
            writeMetaTagsToSidecar=True,
        ),
        enforced_rating=5,
    )()

    assert not exists(fullname)
    assert exists(join(dst, groupname, "test.JPG"))

    with ExifToolHelper() as et:
        rating = et.get_tags(join(dst, groupname, "test.xmp"), [MowTag.rating.value])[0]
        assert MowTag.rating.value in rating
        assert rating[MowTag.rating.value] == 5
