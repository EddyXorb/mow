import shutil
from os.path import join, exists
import os
from exiftool import ExifToolHelper

from ..modules.mow.mowtags import MowTags
from ..modules.general.medialocalizer import GpsData, MediaLocalizer, LocalizerInput


testfolder = "tests"
src = os.path.abspath(join(testfolder, "filestotreat"))
dst = os.path.abspath("./tests/test_treated")
targetDir = join(dst, "subsubfolder")
imagename = "test3.JPG"
srcfile = join(src, "subsubfolder", imagename)
expectedTransitionedFile = join(dst, "subsubfolder", imagename)


# def executeConversionWith(deleteOriginals=True, maintainFolderStructure=True):
#     MediaLocalizer(
#         LocalizerInput(
#             src=src,
#             dst=dst,
#             deleteOriginals=deleteOriginals,
#             maintainFolderStructure=maintainFolderStructure,

#         )
#     )()


def prepareTest():
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(srcfile))
    shutil.copy(
        join(testfolder, "test3.JPG"),
        srcfile,
    )


def test_force_gps_works():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            force_gps_data=GpsData(lat=1.0, lon=-2.0, elev=3.0),
        )
    )()

    assert not exists(srcfile)
    assert exists(expectedTransitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(expectedTransitionedFile, MowTags.gps_all, params=["-n"])[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTags.gps_latitude] == 1.0
        assert tags[MowTags.gps_longitude] == -2.0
        assert tags[MowTags.gps_elevation_read_only] == 3.0
