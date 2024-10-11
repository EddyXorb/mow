from pathlib import Path
import shutil
from os.path import join, exists
import os

import yaml

from ..modules.general.mediatransitioner import TransitionerInput
from ..modules.image.imageconverter import ImageConverter
from ..modules.image.imagerenamer import *

testfolder = (Path(__file__).parent.parent / "tests").absolute().__str__()
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_converted")
imagename = "test.jpg"
srcfile = join(src, "subsubfolder", imagename)
targetDir = join(dst, "subsubfolder")
expectedConvertedImageFile = join(targetDir, imagename)


def executeConversionWith(maintainFolderStructure=True):
    with open(Path(__file__).parent.parent / ".mow_test_settings.yml") as f:
        settings = yaml.safe_load(f)

    ImageConverter(
        TransitionerInput(
            src=src,
            dst=dst,
            maintainFolderStructure=maintainFolderStructure,
            settings=settings,
        )
    )()


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join(testfolder, "test.jpg"),
        os.path.dirname(srcfile),
    )
    shutil.copy(
        join(testfolder, "test.ORF"),
        os.path.dirname(srcfile),
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
    assert exists(join(src, "deleted", "subsubfolder", "test.ORF"))

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
    assert not exists(join(src, "deleted", "subsubfolder", "test.dng"))