from pathlib import Path
from ..modules.mow import mowtags
from ..modules.mow.mowtags import MowTags, MowTag, MowTagFileManipulator
import shutil
from os.path import dirname, join, abspath
import os
from exiftool import ExifToolHelper

testfolder = Path("tests").absolute()
basefile = testfolder / "test.JPG"
src = testfolder / "filestotreat"
testfile = src / "test.JPG"

complex_tags = {
    MowTag.rating: 5,
    MowTag.description: "test",
    MowTag.stagehistory: ["test1", "test2"],
    MowTag.hierarchicalsubject: '{"test": {"test2": "test3"}}',
    MowTag.gps_elevation: 100.1,
    MowTag.gps_latitude: 1.1,
    MowTag.gps_longitude: 2.2,
}


def prepareTest(folder=src):
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    shutil.copy(basefile, testfile)


def test_read_tags_mowfilemanipulator():
    prepareTest()
    fm = MowTagFileManipulator()
    result = fm.readTags(testfile, tags=[MowTag.rating])
    assert result is not None
    assert MowTag.rating in result
    assert result[MowTag.rating] == 2
    assert len(result) == 1

    result = fm.readTags(testfile, tags=[])
    assert result is not None
    assert len(result) == 0


def test_write_tags_simple_mowfilemanipulator():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.writeTags(
        testfile,
        {MowTag.rating: 5},
    )
    result = fm.readTags(testfile, tags=[MowTag.rating])
    assert result is not None
    assert MowTag.rating in result
    assert result[MowTag.rating] == 5


def test_complex_write_tags_mowfilemanipulator():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.writeTags(testfile, complex_tags)
    result = fm.readTags(
        testfile,
        tags=[
            MowTag.rating,
            MowTag.description,
            MowTag.stagehistory,
            MowTag.hierarchicalsubject,
            MowTag.gps_elevation,
            MowTag.gps_latitude,
            MowTag.gps_longitude,
        ],
    )
    for tag in complex_tags.keys():
        assert tag in result
        assert result[tag] == complex_tags[tag]


def test_negative_gps_elevation_works():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.writeTags(
        testfile,
        {MowTag.gps_elevation: -100},
    )
    result = fm.readTags(testfile, tags=[MowTag.gps_elevation])
    assert result[MowTag.gps_elevation] == -100


def test_write_to_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()
    sidecar = fm.write_to_sidecar(testfile, {MowTag.rating: 1})
    assert sidecar is not None
    assert sidecar.exists()
    assert sidecar.stat().st_size > 0

    result = fm.readTags(sidecar, tags=[MowTag.rating])
    assert result is not None
    assert MowTag.rating in result
    assert result[MowTag.rating] == 1
    assert len(result) == 1


def test_overwrite_sidecar_works():
    prepareTest()

    fm = MowTagFileManipulator()

    sidecar = fm.write_to_sidecar(testfile, {MowTag.rating: 2})

    result = fm.readTags(sidecar, tags=[MowTag.rating])

    assert result[MowTag.rating] == 2
    sidecar = fm.write_to_sidecar(testfile, {MowTag.rating: 1})

    result = fm.readTags(sidecar, tags=[MowTag.rating])
    assert result[MowTag.rating] == 1


def test_overwrite_sidecar_partially_works():
    prepareTest()

    fm = MowTagFileManipulator()

    sidecar = fm.write_to_sidecar(
        testfile, {MowTag.rating: 2, MowTag.description: "test"}
    )

    result = fm.readTags(sidecar, tags=[MowTag.rating])

    assert result[MowTag.rating] == 2
    sidecar = fm.write_to_sidecar(testfile, {MowTag.rating: 1})

    result = fm.readTags(sidecar, tags=[MowTag.rating, MowTag.description])
    assert MowTag.description in result
    assert result[MowTag.description] == "test"


def test_read_from_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()

    tags = {MowTag.rating: 2, MowTag.description: "test"}
    fm.write_to_sidecar(testfile, tags)

    read_tags = fm.read_from_sidecar(testfile, tags=tags.keys())

    assert read_tags == tags


def test_merge_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()

    tags = {MowTag.rating: 1, MowTag.description: "test"}
    fm.write_to_sidecar(testfile, tags)

    fm.merge_sidecar_into_file(testfile)
    read_tags = fm.readTags(testfile, tags=tags.keys())
    assert not (testfile.with_suffix(".xmp")).exists()
    assert read_tags == tags


def test_create_sidecar_from_file():
    prepareTest()
    fm = MowTagFileManipulator()

    sidecar = fm.create_sidecar_from_file(testfile)
    assert sidecar.exists()
    assert sidecar.stat().st_size > 0

    read_tags = fm.readTags(testfile, tags=mowtags.tags_all)
    read_tags_sidecar = fm.readTags(sidecar, tags=mowtags.tags_all)

    assert read_tags == read_tags_sidecar
