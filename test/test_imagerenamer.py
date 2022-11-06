from datetime import datetime
from ..image.imagerenamer import *
import shutil
from os.path import join

tempsrcfolder = "filestorename"
src = os.path.abspath(join("test", tempsrcfolder))
dst = os.path.abspath("./test/test_renamed")
targetDir = join(dst, "subsubfolder")
srcfile = join(src, "subsubfolder", "test3.JPG")


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join("test", "test3.JPG"),
        srcfile,
    )


def test_subfolderaremaintained():
    prepareTest()

    renamer = ImageRenamer(
        src,
        dst,
        recursive=True,
        move=False,
        restoreOldNames=False,
        verbose=True,
        maintainFolderStructure=True,
        dry=True,
    )
    renamer()
    print(renamer.oldToNewMapping)

    assert len(renamer.toTreat) == 1
    for old, new in renamer.oldToNewMapping.items():
        print(old, new)
        assert os.path.dirname(srcfile) in old
        assert join("test", "test_renamed", "subsubfolder") in new


def test_copyworks():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should contain only one file

    renamer = ImageRenamer(
        src,
        dst,
        recursive=True,
        move=False,
        restoreOldNames=False,
        verbose=True,
        maintainFolderStructure=True,
        dry=False,
    )

    renamer()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should still contain only one file
    assert len(os.listdir(targetDir)) == 1  # should contain a new file after copying


def test_moveworks():
    prepareTest()

    assert (
        len(os.listdir(join(src, "subsubfolder"))) == 1
    )  # source should contain only one file

    renamer = ImageRenamer(
        src,
        dst,
        recursive=True,
        move=True,
        restoreOldNames=False,
        verbose=True,
        maintainFolderStructure=True,
        dry=False,
    )

    renamer()

    assert (
        len(os.listdir(os.path.dirname(srcfile))) == 0
    )  # source should still contain only one file
    assert len(os.listdir(targetDir)) == 1  # should contain a new file after copying


def test_nonemptyDestinationIsNoProblem():
    prepareTest()
    os.makedirs(dst, exist_ok=True)
    renamer = ImageRenamer(
        src,
        dst,
        recursive=True,
        move=True,
        restoreOldNames=False,
        verbose=True,
        maintainFolderStructure=True,
        dry=False,
    )
    renamer()
    
    assert len(os.listdir(targetDir)) == 1  # should contain a new file after copying
    
def test_timeStampIsCorrect():
    prepareTest()
    
    os.makedirs(dst, exist_ok=True)
    renamer = ImageRenamer(
        src,
        dst,
        recursive=True,
        move=True,
        restoreOldNames=False,
        verbose=True,
        maintainFolderStructure=True,
        dry=False,
    )
    renamer()
    
    for old,new in renamer.oldToNewMapping.items():
        timestamp = os.path.basename(new).split("_")[0] #we assume YYYY-MM-DD@HHMMSS_OLDNAME e.g. "2022-07-27@215555_test3"
        assert(len(timestamp) == 17)
        dt = datetime.strptime(timestamp,"%Y-%m-%d@%H%M%S")
        
        
        
