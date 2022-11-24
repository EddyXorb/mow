import shutil
from os.path import join, exists, splitext, abspath
import os
from time import sleep

from ..modules.image.imageaggregator import (
    ImageAggregator,
    TransitionerInput,
    ImageFile,
)
from pathlib import Path
from exiftool import ExifToolHelper, ExifTool

import logging


testsfolder = abspath("tests")

src = os.path.abspath(join(testsfolder, "filestotreat"))
dst = os.path.abspath(join(testsfolder, "test_treated"))

testfile = join(src, "test_aggregate.jpg")

testfilejpg = join(testsfolder, "test_aggregate.jpg")
testfileraw = join(testsfolder, "test_aggregate.ORF")


def prepareTest(srcname="test.JPG"):
    if not exists(testfilejpg) or not exists(testfileraw):
        shutil.copy(join(testsfolder, "test.jpg"), testfilejpg)
        shutil.copy(join(testsfolder, "test.ORF"), testfileraw)
        with ExifToolHelper() as et:
            result = et.set_tags(
                [testfilejpg, testfileraw],
                {
                    "XMP:Rating": 4,
                    "XMP:Date": "2022:07:27 21:55:55",
                    "XMP:Source": "test_aggregate.jpg",
                    "XMP:Description": "2022-12-12@121212_TEST",
                },
                params=["-P", "-overwrite_original", "-v2"],
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


def test_wrongTimestampOfFileIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "202-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_wrongTimestampOfGroupIsRecognized():
    groupname = "202-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_tooshortGroupnameIsRecognized():
    groupname = "2022-12-12@121212"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_differentXMPTagsBetweenJPGandRawAreRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    with ExifToolHelper() as et:
        et.set_tags(
            fullname,
            {"XMP:Source": "IamDifferent"},
            params=["-P", "-overwrite_original"],
        )

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_missingXMPTagSourceInRawIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.ORF")
    prepareTest(srcname=fullname)

    with ExifTool() as et:
        et.execute("-xmp:source=", "-P", "-overwrite_original", fullname)

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_missingXMPTagSourceInJpgIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    with ExifTool() as et:
        et.execute("-xmp:source=", "-P", "-overwrite_original", fullname)

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_missingXMPTagDescriptionIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    # delete tag
    with ExifTool() as et:
        et.execute(
            "-xmp:Description=", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_missingXMPTagDateIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute("-xmp:Date=", "-P", "-overwrite_original", *ifile.getAllFileNames())

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_missingXMPTagRatingIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def test_rating1ImageIsMovedIntoDeleteFolder():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=1", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert not exists(fullname)
    assert not exists(fullname.replace(".jpg", ".ORF"))

    assert not exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )

    assert exists(join(src, "deleted", str(Path(fullname).relative_to(src))))
    assert exists(
        join(src, "deleted", str(Path(fullname.replace("jpg", "ORF")).relative_to(src)))
    )


def test_rating2ImagesRawIsMovedIntoDeleteFolderJpgTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=2", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert not exists(fullname)
    assert not exists(fullname.replace(".jpg", ".ORF"))

    assert exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )

    assert not exists(join(src, "deleted", str(Path(fullname).relative_to(src))))
    assert exists(
        join(src, "deleted", str(Path(fullname.replace("jpg", "ORF")).relative_to(src)))
    )


def test_rating3ImagesRawIsMovedIntoDeleteFolderJpgTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=3", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert exists(fullname)
    assert exists(fullname.replace(".jpg", ".ORF"))

    ImageAggregator(
        input=TransitionerInput(src=src, dst=dst, dry=False, verbose=True)
    )()

    assert not exists(fullname)
    assert not exists(fullname.replace(".jpg", ".ORF"))
    assert exists(join(dst, str(Path(fullname).relative_to(src))))
    assert not exists(
        join(dst, str(Path(fullname.replace(".jpg", ".ORF")).relative_to(src)))
    )

    assert not exists(join(src, "deleted", str(Path(fullname).relative_to(src))))
    assert exists(
        join(src, "deleted", str(Path(fullname.replace("jpg", "ORF")).relative_to(src)))
    )


def test_rating4BothImagefilesAreTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=4", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

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

    assert not exists(join(src, "deleted", str(Path(fullname).relative_to(src))))
    assert not exists(
        join(src, "deleted", str(Path(fullname.replace("jpg", "ORF")).relative_to(src)))
    )


def test_rating5BothImagefilesAreTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    args = [
        "-xmp:Rating=5",
        "-P",
        "-overwrite_original",
        "-v2",
        *ifile.getAllFileNames(),
    ]
    logging.info(args)
    with ExifTool() as et:
        logging.info(et.execute(*args))

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

    assert not exists(join(src, "deleted", str(Path(fullname).relative_to(src))))
    assert not exists(
        join(src, "deleted", str(Path(fullname.replace("jpg", "ORF")).relative_to(src)))
    )