import time
from pathlib import Path
import shutil
from os.path import join, exists
import os

import yaml

from ..modules.general.mediatransitioner import TransitionerInput
from ..modules.image.imageconverter import ImageConverter
from ..modules.general.mediatransitioner import DELETE_FOLDER_NAME

testfolder = (Path(__file__).parent.parent / "tests").absolute().__str__()
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_converted")
imagename = "test.jpg"
srcfile = join(src, "subsubfolder", imagename)
targetDir = join(dst, "subsubfolder")
expectedConvertedImageFile = join(targetDir, imagename)


def executeConversionWith(
    maintainFolderStructure=True, filterstring="", jpg_quality=100
):
    with open(Path(__file__).parent.parent / ".mow_test_settings.yml") as f:
        settings = yaml.safe_load(f)

    ImageConverter(
        TransitionerInput(
            src=src,
            dst=dst,
            maintainFolderStructure=maintainFolderStructure,
            settings=settings,
            filter=filterstring,
        ),
        jpg_quality=jpg_quality,
    )()


def prepareTest(n: int = 1):
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    for i in range(0, n):
        shutil.copy(
            join(testfolder, "test.jpg"),
            os.path.join(os.path.dirname(srcfile), f"test{i if n > 1 else ''}.jpg"),
        )
        shutil.copy(
            join(testfolder, "test.ORF"),
            os.path.join(os.path.dirname(srcfile), f"test{i if n > 1 else ''}.ORF"),
        )


def test_moveworks():
    prepareTest()

    executeConversionWith()

    assert not exists(srcfile)
    assert exists(expectedConvertedImageFile)


def test_disablemaintainfolderstructureworks():
    prepareTest()

    executeConversionWith(maintainFolderStructure=False)

    assert not exists(srcfile)
    assert exists(join(dst, imagename))


def test_dng_conversion_works():
    prepareTest()

    executeConversionWith()

    assert not exists(srcfile)
    assert exists(join(dst, "subsubfolder", imagename))
    assert exists(join(dst, "subsubfolder", os.path.splitext(imagename)[0] + ".dng"))
    assert exists(join(src, DELETE_FOLDER_NAME, "subsubfolder", "test.ORF"))


def test_dng_conversion_does_not_convert_dng_again():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join(testfolder, "test.jpg"),
        os.path.dirname(srcfile),
    )
    shutil.copy(
        join(testfolder, "test.dng"),
        os.path.dirname(srcfile),
    )

    executeConversionWith()

    assert not exists(srcfile)
    assert exists(join(dst, "subsubfolder", imagename))
    assert exists(join(dst, "subsubfolder", os.path.splitext(imagename)[0] + ".dng"))
    assert not exists(join(src, DELETE_FOLDER_NAME, "subsubfolder", "test.dng"))


def test_dng_conversion_is_multithreaded():
    n = 5
    prepareTest(n)

    start = time.time()
    for i in range(0, n):
        executeConversionWith(filterstring=f"test{i}")
    duration_singlethreaded = time.time() - start

    for i in range(0, n):
        assert not exists(join(src, "subsubfolder", f"test{i}.jpg"))
        assert exists(join(dst, "subsubfolder", f"test{i}.jpg"))
        assert exists(join(dst, "subsubfolder", f"test{i}.dng"))
        assert exists(join(src, DELETE_FOLDER_NAME, "subsubfolder", f"test{i}.ORF"))

    prepareTest(n)

    start = time.time()
    executeConversionWith()
    duration_multithreaded = time.time() - start

    for i in range(0, n):
        assert not exists(join(src, "subsubfolder", f"test{i}.jpg"))
        assert exists(join(dst, "subsubfolder", f"test{i}.jpg"))
        assert exists(join(dst, "subsubfolder", f"test{i}.dng"))
        assert exists(join(src, DELETE_FOLDER_NAME, "subsubfolder", f"test{i}.ORF"))

    print(
        f"Singlethreaded: {duration_singlethreaded}, Multithreaded: {duration_multithreaded}"
    )

    assert duration_singlethreaded / n > duration_multithreaded / 2


def test_jpg_quality_10_reduces_filessize_notably():
    prepareTest()

    filesize_before = os.path.getsize(srcfile)

    executeConversionWith(jpg_quality=10)

    filesize_after = os.path.getsize(expectedConvertedImageFile)

    assert filesize_after < filesize_before / 2


def test_jpg_quality_100_lets_jpg_unchanged():
    prepareTest()

    filesize_before = os.path.getsize(srcfile)

    executeConversionWith(jpg_quality=100)

    filesize_after = os.path.getsize(expectedConvertedImageFile)

    assert abs(filesize_after - filesize_before) < 1000 # bytes

def test_jpg_quality_10_moves_jpg_into_deleted_folder():
    prepareTest()

    executeConversionWith(jpg_quality=10)

    assert not exists(srcfile)
    assert exists(join(src, DELETE_FOLDER_NAME, "subsubfolder", imagename))
