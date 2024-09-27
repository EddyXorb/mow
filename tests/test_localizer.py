import datetime
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
IMAGENAME = "2022-01-01@101015.JPG"

untransitionedFile = join(src, "subsubfolder", IMAGENAME)
transitionedFile = join(dst, "subsubfolder", IMAGENAME)


def prepareTest(image_name=IMAGENAME):
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(untransitionedFile))
    shutil.copy(
        join(testfolder, "test3.JPG"),
        join(src, "subsubfolder", image_name),
    )
    if not os.path.exists(join(src, "test.gpx")):
        shutil.copy(join(testfolder, "test.gpx"), join(src, "test.gpx"))


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

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(transitionedFile, MowTags.gps_all, params=["-n"])[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTags.gps_latitude] == 1.0
        assert tags[MowTags.gps_longitude] == -2.0
        assert tags[MowTags.gps_elevation_read_only] == 3.0


# The gpx data in test-gpx looks like this:
#
# <trkseg>
#   <trkpt lat="10" lon="-10">
#     <ele>1000</ele>
#     <time>2022-01-01T10:10:10Z</time>
#   </trkpt>
#   <trkpt lat="20" lon="10">
#     <ele>2000</ele>
#     <time>2022-01-01T10:10:20Z</time>
#   </trkpt>
# </trkseg>


def test_no_gps_data_leads_to_no_transition():
    image = "2099-11-11@444444.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
        )
    )()

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_correct_gps_data_leads_to_transition_and_interpolation():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
        )
    )()
    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(transitionedFile, MowTags.gps_all)[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTags.gps_latitude] == 15
        assert tags[MowTags.gps_longitude] == 0
        assert tags[MowTags.gps_elevation_read_only] == 1500


def test_timezone_change_leads_to_no_gps_found():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="Europe/Berlin",
        )
    )()

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_time_image_offset_works():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="Europe/Berlin",  # +1 hours offset to UTC
            time_offset_mediafile=datetime.timedelta(
                hours=+1
            ),  # here we add the offset again
        )
    )()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)


def test_transition_even_if_no_gps_data_works():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="Europe/Berlin",  # +1 hours offset to UTC
            transition_even_if_no_gps_data=True,  # here we add the offset again
        )
    )()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)


def test_gps_time_tolerance_when_too_small_avoids_transition():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
            gps_time_tolerance=datetime.timedelta(seconds=4),
        )
    )()

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_gps_time_tolerance_when_big_enough_transitions():
    prepareTest()

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
            gps_time_tolerance=datetime.timedelta(seconds=5),
        )
    )()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)


def test_image_made_before_first_gps_entry_works():
    image = "2022-01-01@101005.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
            gps_time_tolerance=datetime.timedelta(seconds=10),
        )
    )()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(transitionedFile, MowTags.gps_all)[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTags.gps_latitude] == 10
        assert tags[MowTags.gps_longitude] == -10
        assert tags[MowTags.gps_elevation_read_only] == 1000


def test_image_made_before_first_gps_entry_but_too_small_tolerance_does_not_transition():
    image = "2022-01-01@101005.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
            gps_time_tolerance=datetime.timedelta(seconds=2),
        )
    )()

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_image_made_after_last_gps_entry_works():
    image = "2022-01-01@101025.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
            gps_time_tolerance=datetime.timedelta(seconds=5),
        )
    )()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(transitionedFile, MowTags.gps_all)[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTags.gps_latitude] == 20
        assert tags[MowTags.gps_longitude] == 10
        assert tags[MowTags.gps_elevation_read_only] == 2000


def test_image_made_after_last_gps_entry_but_too_small_tolerance_does_not_transition():
    image = "2022-01-01@101025.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    MediaLocalizer(
        LocalizerInput(
            src=src,
            dst=dst,
            deleteOriginals=True,
            maintainFolderStructure=True,
            mediafile_timezone="UTC",
            gps_time_tolerance=datetime.timedelta(seconds=2),
        )
    )()

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)
