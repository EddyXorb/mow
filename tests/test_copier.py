import os
from os.path import join, abspath, dirname, exists
import shutil

from ..modules.general.mediatransitioner import TransitionerInput
from ..modules.general.mediacopier import MediaCopier

testfolder = abspath(dirname(__file__))
tempsrcfolder = "filestotreat"
src = abspath(join(testfolder, tempsrcfolder))
dst = abspath(join(testfolder, "test_treated"))
dummyfile = join(testfolder, "test.jpg")


def prepareTest(last_index=1, max_index=2, raw_has_LAST=True):
    """
    If last_index is bigger than max_index does not create LAST.
    """
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    print(f"Create {src}")
    os.makedirs(src)

    for i in range(0, last_index):
        shutil.copy(dummyfile, join(src, f"test_{i:02}.jpg"))
        shutil.copy(dummyfile, join(src, f"test_{i:02}.ORF"))

    if last_index <= max_index:
        shutil.copy(dummyfile, join(src, f"test_{last_index:02}_LAST.jpg"))
        shutil.copy(
            dummyfile,
            join(src, f"test_{last_index:02}{'_LAST' if raw_has_LAST else ''}.ORF"),
        )

    for i in range(last_index + 1, max_index + 1):
        shutil.copy(dummyfile, join(src, f"test_{i:02}.jpg"))
        shutil.copy(dummyfile, join(src, f"test_{i:02}.ORF"))


def test_dummy():
    prepareTest(1, 2, True)


def test_missing_LAST_implies_copying_everything():
    prepareTest(3, 2)

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    for i in range(0, 3):
        assert exists(join(dst, f"test_{i:02}.jpg"))
        assert exists(join(dst, f"test_{i:02}.ORF"))


def test_LAST_is_moved_to_end():
    prepareTest(1, 2)

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    assert exists(join(src, f"test_01.jpg"))
    assert exists(join(src, f"test_01.ORF"))
    assert not exists(join(src, f"test_01_LAST.jpg"))
    assert not exists(join(src, f"test_01_LAST.ORF"))
    assert exists(join(src, f"test_02_LAST.jpg"))
    assert exists(join(src, f"test_02_LAST.ORF"))

    prepareTest(1, 2, False)

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    assert exists(join(src, f"test_01.jpg"))
    assert exists(join(src, f"test_01.ORF"))
    assert not exists(join(src, f"test_01_LAST.jpg"))
    assert not exists(join(src, f"test_01_LAST.ORF"))
    assert exists(join(src, f"test_02_LAST.jpg"))
    assert exists(join(src, f"test_02_LAST.ORF"))


def test_nothing_before_LAST_is_copied():
    prepareTest(5, 10)

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    for i in range(0, 6):
        assert not exists(join(dst, f"test_{i:02}.jpg"))
        assert not exists(join(dst, f"test_{i:02}.ORF"))


def test_all_after_LAST_are_copied():
    prepareTest(5, 10)

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    for i in range(6, 11):
        assert exists(join(dst, f"test_{i:02}.jpg"))
        assert exists(join(dst, f"test_{i:02}.ORF"))


def test_does_not_delete_any_file_in_src():
    for i in range(0, 6):
        prepareTest(i, 5)

        MediaCopier(TransitionerInput(src=src, dst=dst))()

        assert len(os.listdir(src)) == 12


def test_nothing_done_if_LAST_at_end():
    prepareTest(10, 10)

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    assert len(os.listdir(dst)) == 0


def test_missing_LAST_for_ORF_raw_implies_copying_of_that_raw_with_ORF():
    prepareTest(2, 3, False)

    assert exists(join(src, "test_02_LAST.jpg"))
    assert exists(join(src, "test_02.ORF"))

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    assert exists(join(dst, "test_02.ORF"))


def test_missing_LAST_for_DNG_raw_does_imply_copying_of_that_raw_with_DNG():
    prepareTest(2, 3, False)
    shutil.move(join(src, "test_02.ORF"), join(src, "test_02.DNG"))

    assert exists(join(src, "test_02_LAST.jpg"))
    assert exists(join(src, "test_02.DNG"))

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    assert exists(join(dst, "test_02.DNG"))


def test_LAST_is_not_copied():
    prepareTest(5, 10)

    assert exists(join(src, f"test_05_LAST.jpg"))
    assert exists(join(src, f"test_05_LAST.ORF"))

    MediaCopier(TransitionerInput(src=src, dst=dst))()

    assert not exists(join(dst, f"test_05_LAST.jpg"))
    assert not exists(join(dst, f"test_05_LAST.ORF"))
    assert not exists(join(dst, f"test_05.jpg"))
    assert not exists(join(dst, f"test_05.ORF"))
