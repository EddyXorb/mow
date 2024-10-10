import shutil
from os.path import join, exists
import os

from ..modules.general.mediatransitioner import TransitionerInput
from ..modules.image.imageconverter import ImageConverter
from ..modules.image.imagerenamer import *

testfolder = "tests"
tempsrcfolder = "filestotreat"
src = os.path.abspath(join(testfolder, tempsrcfolder))
dst = os.path.abspath("./tests/test_converted")
targetDir = join(dst, "subsubfolder")
imagename = "test3.JPG"
srcfile = join(src, "subsubfolder", imagename)
expectedConvertedImageFile = join(dst, "subsubfolder", imagename)


def executeConversionWith(maintainFolderStructure=True):
    ImageConverter(
        TransitionerInput(
            src=src,
            dst=dst,
            maintainFolderStructure=maintainFolderStructure,
        )
    )()


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join(testfolder, "test3.JPG"),
        srcfile,
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
