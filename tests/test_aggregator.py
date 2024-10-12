from dataclasses import dataclass
import shutil
from os.path import join, exists, splitext, abspath
import os
from time import sleep


from ..modules.general.mediatransitioner import DELETE_FOLDER_NAME
from ..modules.general.mediaaggregator import AggregatorInput
from ..modules.image.imageaggregator import (
    ImageAggregator,
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


@dataclass
class Cached:
    xmp_description: str = "2022-12-12@121212_TEST"
    need_to_init: bool = True


cached = Cached()


def prepareTest(srcname="test.JPG", xmp_description="2022-12-12@121212_TEST"):
    """
    Here we create a test_aggregate version of each file, which we cache in 'testsfolder'. Without caching, we had to call exiftoolhelper too often which would slowdown a lot.
    """
    if (
        not exists(testfilejpg)
        or not exists(testfileraw)
        or (xmp_description != cached.xmp_description)
        or cached.need_to_init
    ):
        shutil.copy(join(testsfolder, "test.jpg"), testfilejpg)
        shutil.copy(join(testsfolder, "test.ORF"), testfileraw)

        prepareXMPData(xmp_description)
        cached.xmp_description = xmp_description
        cached.need_to_init = False

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


def prepareXMPData(description):
    with ExifToolHelper() as et:
        result = et.set_tags(
            [testfilejpg, testfileraw],
            {
                "XMP:Rating": 4,
                "XMP:Date": "2022:07:27 21:55:55",
                "XMP:Source": "test_aggregate.jpg",
                "XMP:Description": description,
            },
            params=["-P", "-overwrite_original", "-v2"],
        )
    logging.info(result)


def bothFilesAreInSRC(jpgname):
    return exists(jpgname) and exists(jpgname.replace(".jpg", ".ORF"))


def bothFilesAreNOTinSRC(jpgname):
    return not exists(jpgname) and not exists(jpgname.replace(".jpg", ".ORF"))


def bothFilesAreInDST(jpgname):
    return jpgIsInDST(jpgname) and rawIsInDST(jpgname)


def bothFilesAreNOTInDST(jpgname):
    return not jpgIsInDST(jpgname) and not rawIsInDST(jpgname)


def jpgIsInDST(jpgname):
    return exists(join(dst, str(Path(jpgname).relative_to(src))))


def rawIsInDST(jpgname):
    return exists(
        join(dst, str(Path(jpgname.replace(".jpg", ".ORF")).relative_to(src)))
    )


def transitionTookPlace(jpgname):
    return bothFilesAreNOTinSRC(jpgname) and bothFilesAreInDST(jpgname)


def assertTransitionTookNOTPlace(jpgname):
    return bothFilesAreInSRC(jpgname) and bothFilesAreNOTInDST(jpgname)


def jpgWasDeleted(jpgname):
    return exists(join(src, DELETE_FOLDER_NAME, str(Path(jpgname).relative_to(src))))


def rawWasDeleted(jpgname):
    return exists(
        join(src, DELETE_FOLDER_NAME, str(Path(jpgname.replace("jpg", "ORF")).relative_to(src)))
    )


def bothWereNotDeleted(fullname):
    return not jpgWasDeleted(fullname) and not rawWasDeleted(fullname)


def test_correctImageIsTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")

    prepareTest(srcname=fullname)
    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert transitionTookPlace(fullname)


def test_wrongTimestampOfFileIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "202-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_wrongTimestampOfGroupIsRecognized():
    groupname = "202-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_wrongDescriptionTagIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname, xmp_description=groupname + "_I_AM_DIFFERENT")

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_tooshortGroupnameIsRecognized():
    groupname = "2022-12-12@121212"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


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

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_jpgSingleSourceOfTruthWorks():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    with ExifToolHelper() as et:
        et.set_tags(
            fullname,
            {"XMP:Source": "IamDifferent"},
            params=["-P", "-overwrite_original"],
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(
        input=AggregatorInput(
            src=src, dst=dst, dry=False, verbose=True, jpgSingleSourceOfTruth=True
        )
    )()

    assert transitionTookPlace(fullname)


def test_missingXMPTagSourceInRawIsCopiedFromJpg():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.ORF")
    prepareTest(srcname=fullname)

    with ExifTool() as et:
        et.execute("-xmp:source=", "-P", "-overwrite_original", fullname)

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(
        input=AggregatorInput(
            src=src, dst=dst, dry=False, verbose=True, writeMetaTags=True
        )
    )()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg.replace(".jpg", ".ORF"), "XMP:Source")[0]
        assert tag["XMP:Source"] == "test_aggregate.jpg"


def test_missingXMPTagSourceInJpgIsCopiedFromRaw():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)

    with ExifTool() as et:
        et.execute("-xmp:source=", "-P", "-overwrite_original", fullname)

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg, "XMP:Source")[0]
        assert tag["XMP:Source"] == "test_aggregate.jpg"


def test_missingXMPTagDescriptionIsCopiedFromRaw():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    # delete tag
    with ExifTool() as et:
        et.execute("-xmp:Description=", "-P", "-overwrite_original", str(ifile))

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg, "XMP:Description")[0]
        assert tag["XMP:Description"] == "2022-12-12@121212_TEST"


def test_completelyMissingXMPTagDescriptionIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    # delete tag
    with ExifTool() as et:
        et.execute(
            "-xmp:Description=", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_completelyMissingXMPTagDateIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute("-xmp:Date=", "-P", "-overwrite_original", *ifile.getAllFileNames())

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_missingXMPTagDateIsCopiedFromRaw():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute("-xmp:Date=", "-P", "-overwrite_original", str(ifile))

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))
    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg, "XMP:Date")[0]
        assert tag["XMP:Date"] == "2022:07:27 21:55:55"


def test_completelyMissingXMPTagRatingIsRecognized():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assertTransitionTookNOTPlace(fullname)


def test_missingXMPTagRatingIsCopiedFromRaw():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute("-xmp:Rating=", "-P", "-overwrite_original", str(ifile))

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))
    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg, "XMP:Rating")[0]
        assert tag["XMP:Rating"] == 4


def test_optionalXMPTagLabelIsCopiedFromJpg():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifToolHelper() as et:
        et.set_tags(
            tags={"XMP:Label": "Green"},
            params=["-P", "-overwrite_original"],
            files=str(ifile),
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg.replace(".jpg", ".ORF"), "XMP:Label")[0]
        assert tag["XMP:Label"] == "Green"


def test_optionalXMPTagSubjectIsCopiedFromJpg():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute("-xmp:Subject=Haus", "-P", "-overwrite_original", str(ifile))

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg.replace(".jpg", ".ORF"), "XMP:Subject")[0]
        assert tag["XMP:Subject"] == "Haus"


def test_optionalXMPTagHierarchicalSubjectIsCopiedFromJpg():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:HierarchicalSubject=Project|Haus",
            "-P",
            "-overwrite_original",
            str(ifile),
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(
            expectedTargetJpg.replace(".jpg", ".ORF"), "XMP:HierarchicalSubject"
        )[0]
        assert tag["XMP:HierarchicalSubject"] == "Project|Haus"


def test_multipleHSubjectsAreNoProblem():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifToolHelper() as et:
        et.set_tags(
            str(ifile),
            tags={
                "XMP:Subject": [
                    "Haus",
                    "Buch",
                    "Hubert",
                ]
            },
            params=["-P", "-overwrite_original"],
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(expectedTargetJpg.replace(".jpg", ".ORF"), "XMP:Subject")[0]
        print(tag["XMP:Subject"])
        assert len(tag["XMP:Subject"]) == 3
        assert "Haus" in tag["XMP:Subject"]
        assert "Buch" in tag["XMP:Subject"]
        assert "Hubert" in tag["XMP:Subject"]


def test_multipleHierarchicalSubjectsAreNoProblem():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifToolHelper() as et:
        et.set_tags(
            str(ifile),
            tags={
                "XMP:HierarchicalSubject": [
                    "Project|Haus",
                    "Project|Buch",
                    "Person|Hubert",
                ]
            },
            params=["-P", "-overwrite_original"],
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreInDST(fullname)

    expectedTargetJpg = join(dst, str(Path(fullname).relative_to(src)))

    with ExifToolHelper() as et:
        tag = et.get_tags(
            expectedTargetJpg.replace(".jpg", ".ORF"), "XMP:HierarchicalSubject"
        )[0]
        print(tag["XMP:HierarchicalSubject"])
        assert len(tag["XMP:HierarchicalSubject"]) == 3
        assert "Project|Haus" in tag["XMP:HierarchicalSubject"]
        assert "Project|Buch" in tag["XMP:HierarchicalSubject"]
        assert "Person|Hubert" in tag["XMP:HierarchicalSubject"]


def test_rating1ImageIsMovedIntoDeleteFolder():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=1", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)
    assert bothFilesAreNOTInDST(fullname)
    assert jpgWasDeleted(fullname) and rawWasDeleted(fullname)


def test_rating1Rawrating5jpgAndJPGSingleSourceOfTruthDoesNotDelete():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute("-xmp:Rating=5", "-P", "-overwrite_original", ifile.getJpg())
        et.execute("-xmp:Rating=1", "-P", "-overwrite_original", ifile.getRaw())

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(
        input=AggregatorInput(
            src=src, dst=dst, dry=False, verbose=True, jpgSingleSourceOfTruth=True
        )
    )()

    assert transitionTookPlace(fullname)

    bothWereNotDeleted(fullname)


def test_rating2ImagesRawIsMovedIntoDeleteFolderJpgTransitioned():
    groupname = "2022-12-12@121212_TEST"
    fullname = join(src, groupname, "2022-12-12@121212_test.jpg")
    prepareTest(srcname=fullname)
    ifile = ImageFile(fullname)

    with ExifTool() as et:
        et.execute(
            "-xmp:Rating=2", "-P", "-overwrite_original", *ifile.getAllFileNames()
        )

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)

    assert (
        jpgIsInDST(fullname)
        and not rawIsInDST(fullname)
        and not jpgWasDeleted(fullname)
        and rawWasDeleted(fullname)
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

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert bothFilesAreNOTinSRC(fullname)

    assert (
        jpgIsInDST(fullname)
        and not rawIsInDST(fullname)
        and not jpgWasDeleted(fullname)
        and rawWasDeleted(fullname)
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

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert transitionTookPlace(fullname)
    assert not jpgWasDeleted(fullname) and not rawWasDeleted(fullname)


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

    assert bothFilesAreInSRC(fullname)

    ImageAggregator(input=AggregatorInput(src=src, dst=dst, dry=False, verbose=True))()

    assert transitionTookPlace(fullname)
    assert not jpgWasDeleted(fullname) and not rawWasDeleted(fullname)
