import shutil
from os.path import join, exists
import os

from ..modules.general.mediaconverter import ConverterInput
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


def executeConversionWith(deleteOriginals=True, maintainFolderStructure=True):
    ImageConverter(
        ConverterInput(
            src=src,
            dst=dst,
            deleteOriginals=deleteOriginals,
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

    executeConversionWith(deleteOriginals=True)

    assert not exists(srcfile)
    assert exists(expectedConvertedImageFile)


def test_disablemaintainfolderstructureworks():
    prepareTest()

    executeConversionWith(deleteOriginals=True, maintainFolderStructure=False)

    assert not exists(srcfile)
    assert exists(join(dst, imagename))
