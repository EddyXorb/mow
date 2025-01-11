from pathlib import Path

from modules.image.imagefile import ImageFile
from ..modules.mow import mowtags
from ..modules.mow.mowtags import MowTag, MowTagFileManipulator
import shutil
import os

testfolder = Path("tests").absolute()
basefile = testfolder / "test.JPG"
src = testfolder / "filestotreat"
testfile = Path(src / "test.JPG")
testmfile = ImageFile(testfile)

complex_tags = {
    MowTag.rating: 5,
    MowTag.description: "test",
    MowTag.stagehistory: ["test1", "test2"],
    MowTag.hierarchicalsubject: ["Projekt|Fotobuch|Nonni"],
    MowTag.gps_elevation: 100.1,
    MowTag.gps_latitude: 1.1,
    MowTag.gps_longitude: 2.2,
}


def prepareTest(folder=src, copy_raw=False):
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    shutil.copy(basefile, testfile)
    if copy_raw:
        shutil.copy(basefile.with_suffix(".ORF"), testfile.with_suffix(".ORF"))
    global testmfile
    testmfile = ImageFile(testfile)



def test_read_tags_mowfilemanipulator():
    prepareTest()
    fm = MowTagFileManipulator()
    result = fm.read_tags(testfile, tags=[MowTag.rating])
    assert result is not None
    assert MowTag.rating in result
    assert result[MowTag.rating] == 2
    assert len(result) == 1

    result = fm.read_tags(testfile, tags=[])
    assert result is not None
    assert len(result) == 0


def test_write_tags_simple_mowfilemanipulator():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.write_tags(
        testfile,
        {MowTag.rating: 5},
    )
    result = fm.read_tags(testfile, tags=[MowTag.rating])
    assert result is not None
    assert MowTag.rating in result
    assert result[MowTag.rating] == 5


def test_complex_write_tags_mowfilemanipulator():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.write_tags(testfile, complex_tags)
    result = fm.read_tags(
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


def test_complex_write_tags_mowfilemanipulator_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.write_to_sidecar(testmfile, complex_tags)
    result = fm.read_from_sidecar(
        testmfile,
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
    fm.write_tags(
        testfile,
        {MowTag.gps_elevation: -100},
    )
    result = fm.read_tags(testfile, tags=[MowTag.gps_elevation])
    assert result[MowTag.gps_elevation] == -100

    fm.write_to_sidecar(
        testmfile,
        {MowTag.gps_elevation: -100},
    )
    result = fm.read_from_sidecar(testmfile, tags=[MowTag.gps_elevation])
    assert result[MowTag.gps_elevation] == -100


def test_gps_latitude_longitude_works():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.write_tags(
        testmfile.getAllFileNames()[0],
        {MowTag.gps_latitude: 1.1, MowTag.gps_longitude: 2.2},
    )
    result = fm.read_tags(
        testmfile.getAllFileNames()[0], tags=[MowTag.gps_latitude, MowTag.gps_longitude]
    )
    assert result[MowTag.gps_latitude] == 1.1
    assert result[MowTag.gps_longitude] == 2.2

    fm.write_to_sidecar(
        testmfile,
        {MowTag.gps_latitude: 1.1, MowTag.gps_longitude: 2.2},
    )
    result = fm.read_from_sidecar(
        testmfile, tags=[MowTag.gps_latitude, MowTag.gps_longitude]
    )
    assert result[MowTag.gps_latitude] == 1.1
    assert result[MowTag.gps_longitude] == 2.2


def test_gps_latitude_longitude_negative_works():
    prepareTest()
    fm = MowTagFileManipulator()
    fm.write_tags(
        Path(testfile),
        {MowTag.gps_latitude: -1.1, MowTag.gps_longitude: -2.2},
    )
    result = fm.read_tags(
        Path(testfile), tags=[MowTag.gps_latitude, MowTag.gps_longitude]
    )
    assert result[MowTag.gps_latitude] == -1.1
    assert result[MowTag.gps_longitude] == -2.2

    fm.write_to_sidecar(
        testmfile,
        {MowTag.gps_latitude: -1.1, MowTag.gps_longitude: -2.2},
    )
    result = fm.read_from_sidecar(
        testmfile, tags=[MowTag.gps_latitude, MowTag.gps_longitude]
    )
    assert result[MowTag.gps_latitude] == -1.1
    assert result[MowTag.gps_longitude] == -2.2


def test_write_to_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()
    sidecar = fm.write_to_sidecar(testmfile, {MowTag.rating: 1})
    assert sidecar is not None
    assert sidecar.exists()
    assert sidecar.stat().st_size > 0

    result = fm.read_tags(sidecar, tags=[MowTag.rating])
    assert result is not None
    assert MowTag.rating in result
    assert result[MowTag.rating] == 1
    assert len(result) == 1


def test_overwrite_sidecar_works():
    prepareTest()

    fm = MowTagFileManipulator()

    sidecar = fm.write_to_sidecar(testmfile, {MowTag.rating: 2})

    result = fm.read_tags(sidecar, tags=[MowTag.rating])

    assert result[MowTag.rating] == 2
    sidecar = fm.write_to_sidecar(testmfile, {MowTag.rating: 1})

    result = fm.read_tags(sidecar, tags=[MowTag.rating])
    assert result[MowTag.rating] == 1


def test_overwrite_sidecar_partially_works():
    prepareTest()

    fm = MowTagFileManipulator()

    sidecar = fm.write_to_sidecar(
        testmfile, {MowTag.rating: 2, MowTag.description: "test"}
    )

    result = fm.read_tags(sidecar, tags=[MowTag.rating])

    assert result[MowTag.rating] == 2
    sidecar = fm.write_to_sidecar(testmfile, {MowTag.rating: 1})

    result = fm.read_tags(sidecar, tags=[MowTag.rating, MowTag.description])
    assert MowTag.description in result
    assert result[MowTag.description] == "test"


def test_read_from_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()

    tags = {MowTag.rating: 2, MowTag.description: "test"}
    fm.write_to_sidecar(testmfile, tags)

    read_tags = fm.read_from_sidecar(testmfile, tags=tags.keys())

    assert read_tags == tags


def test_merge_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()

    tags = {MowTag.rating: 1, MowTag.description: "test"}
    fm.write_to_sidecar(testmfile, tags)

    fm.merge_sidecar_into_mediafile(testmfile)

    read_tags = fm.read_tags(testfile, tags=tags.keys())
    assert not (testfile.with_suffix(".xmp")).exists()
    assert read_tags == tags


def test_create_sidecar_from_file():
    prepareTest()
    fm = MowTagFileManipulator()

    sidecar = fm.create_sidecar_from_file(testmfile)
    assert sidecar.exists()
    assert sidecar.stat().st_size > 0

    read_tags = fm.read_tags(testfile, tags=mowtags.tags_all)
    read_tags_sidecar = fm.read_tags(sidecar, tags=mowtags.tags_all)

    read_tags.pop(MowTag.sourcefile)
    read_tags_sidecar.pop(MowTag.sourcefile)
    assert read_tags == read_tags_sidecar


def test_create_manipulate_and_merge_sidecar():
    prepareTest()
    fm = MowTagFileManipulator()

    fm.create_sidecar_from_file(testmfile)

    fm.write_to_sidecar(testmfile, complex_tags)

    fm.merge_sidecar_into_mediafile(testmfile)
    read_tags = fm.read_tags(testfile, tags=list(complex_tags.keys()))

    assert read_tags == complex_tags


def test_merge_sidecar_into_mediafile_with_raw():
    prepareTest(copy_raw=True)
    fm = MowTagFileManipulator()

    fm.write_to_sidecar(testmfile, complex_tags)
    
    fm.merge_sidecar_into_mediafile(testmfile)
    read_tags_jpg = fm.read_tags(testfile, tags=list(complex_tags.keys()))
    read_tags_raw = fm.read_tags(testfile.with_suffix(".ORF"), tags=list(complex_tags.keys()))

    assert read_tags_jpg == complex_tags
    assert read_tags_raw == complex_tags

def test_write_to_mediafile():
    prepareTest(copy_raw=True)
    fm = MowTagFileManipulator()

    fm.write_to_mediafile(testmfile, complex_tags)

    read_tags_jpg = fm.read_tags(testfile, tags=list(complex_tags.keys()))
    read_tags_raw = fm.read_tags(testfile.with_suffix(".ORF"), tags=list(complex_tags.keys()))

    assert read_tags_jpg == complex_tags
    assert read_tags_raw == complex_tags
