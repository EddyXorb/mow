import shutil
from os.path import join, exists, splitext, abspath
import os

from ..modules.image.imageaggregator import ImageAggregator, TransitionerInput
from pathlib import Path
from exiftool import ExifToolHelper

import logging


testsfolder = abspath("tests")

src = os.path.abspath(join(testsfolder, "filestotreat"))
dst = os.path.abspath(join(testsfolder, "test_treated"))

testfile = join(src, "test_aggregate.jpg")

testfilejpg = join(testsfolder, "test_aggregate.jpg")
testfileraw = join(testsfolder, "test_aggregate.ORF")

et = ExifToolHelper()


def prepareTest(srcname="test.JPG"):
    if not exists(testfilejpg) or not exists(testfileraw):
        shutil.copy(join(testsfolder, "test.jpg"), testfilejpg)
        shutil.copy(join(testsfolder, "test.ORF"), testfileraw)
        result = et.set_tags(
            [testfilejpg, testfileraw],
            {
                "XMP:Rating": 3,
                "XMP:Date": "2022:07:27 21:55:55",
                "XMP:Source": "test_aggregate.jpg",
                "XMP:Description": "2022-12-12@121212_TEST",
            },
            params=["-P", "-overwrite_original","-v2"],
        )
        logging.info(result)
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcname))
    shutil.copy(
        join(testsfolder, testfilejpg),
        splitext(srcname)[0] + ".jpg",
    )
    shutil.copy(
        join(testsfolder, testfileraw),
        splitext(srcname)[0] + ".ORF",
    )


def test_correctImageIsTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert not exists(fullname)
    assert not exists(fullname.replace(".jpg", ".ORF"))

    assert exists(join(dst, str(Path(fullname).relative_to(src))))
    assert exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )
