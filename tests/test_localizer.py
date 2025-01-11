import datetime
from pathlib import Path
import shutil
from os.path import join, exists
import os
from exiftool import ExifToolHelper


from ..modules.general.mediatransitioner import TransitionerInput
from ..modules.mow.mowtags import MowTag, tags_gps_all, MowTagFileManipulator
from ..modules.general.medialocalizer import (
    BaseLocalizerInput,
    GpsData,
    MediaLocalizer,
    LocalizerInput,
)


testfolder = "tests"
src = os.path.abspath(join(testfolder, "filestotreat"))
dst = os.path.abspath("./tests/test_treated")
targetDir = join(dst, "subsubfolder")
IMAGENAME = "2022-01-01@101015.JPG"

untransitionedFile = Path(src) / "subsubfolder" / IMAGENAME
transitionedFile = Path(dst) / "subsubfolder" / IMAGENAME


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


def perform_transition(
    mediafile_timezone="UTC",
    gps_time_tolerance=datetime.timedelta(seconds=5),
    force_gps_data=None,
    time_offset_mediafile=None,  # here we add the offset again
    **kwargs,
):
    bli = BaseLocalizerInput(
        suppress_map_open=True,  # we do not want to open a map during unit tests, as it is annoying
        mediafile_timezone=mediafile_timezone,
        gps_time_tolerance=gps_time_tolerance,
    )

    if force_gps_data is not None:
        bli.force_gps_data = force_gps_data
    if time_offset_mediafile is not None:
        bli.time_offset_mediafile = time_offset_mediafile

    for key, value in kwargs.items():
        setattr(bli, key, value)

    MediaLocalizer(
        LocalizerInput(
            bli,
            TransitionerInput(
                maintainFolderStructure=True,
                src=src,
                dst=dst,
                writeMetaTagsToSidecar=True,
            ),
        )
    )()


def test_force_gps_works():
    prepareTest()

    perform_transition(force_gps_data=GpsData(lat=1.0, lon=-2.0, elev=3.0))

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    tags = MowTagFileManipulator().read_tags(transitionedFile.with_suffix(".xmp"), tags_gps_all)
    print(tags)
    assert tags[MowTag.gps_latitude] == 1.0
    assert tags[MowTag.gps_longitude] == -2.0
    assert tags[MowTag.gps_elevation] == 3.0


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

    perform_transition()

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_correct_gps_data_leads_to_transition_and_interpolation():
    prepareTest()

    perform_transition()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(
            transitionedFile.with_suffix(".xmp"), [tag.value for tag in tags_gps_all]
        )[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTag.gps_latitude.value] == 15
        assert tags[MowTag.gps_longitude.value] == 0
        assert tags[MowTag.gps_elevation.value] == 1500


def test_timezone_change_leads_to_no_gps_found():
    prepareTest()

    perform_transition(mediafile_timezone="Europe/Berlin")

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_time_image_offset_works():
    prepareTest()

    perform_transition(
        mediafile_timezone="Europe/Berlin",
        time_offset_mediafile=datetime.timedelta(hours=+1),
    )

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)


def test_transition_even_if_no_gps_data_works():
    prepareTest()

    perform_transition(
        mediafile_timezone="Europe/Berlin", transition_even_if_no_gps_data=True
    )

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)


def test_gps_time_tolerance_when_too_small_avoids_transition():
    prepareTest()

    perform_transition(gps_time_tolerance=datetime.timedelta(seconds=4))

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_gps_time_tolerance_when_big_enough_transitions():
    prepareTest()

    perform_transition(gps_time_tolerance=datetime.timedelta(seconds=5))

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)


def test_image_made_before_first_gps_entry_works():
    image = "2022-01-01@101005.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = Path(dst) / "subsubfolder" / image

    perform_transition(gps_time_tolerance=datetime.timedelta(seconds=10))

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(
            transitionedFile.with_suffix(".xmp"), [tag.value for tag in tags_gps_all]
        )[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTag.gps_latitude.value] == 10
        assert tags[MowTag.gps_longitude.value] == -10
        assert tags[MowTag.gps_elevation.value] == 1000


def test_image_made_before_first_gps_entry_but_too_small_tolerance_does_not_transition():
    image = "2022-01-01@101005.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    perform_transition(gps_time_tolerance=datetime.timedelta(seconds=2))

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


def test_image_made_after_last_gps_entry_works():
    image = "2022-01-01@101025.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = Path(dst) / "subsubfolder"/ image

    perform_transition()

    assert not exists(untransitionedFile)
    assert exists(transitionedFile)

    with ExifToolHelper() as et:
        tags = et.get_tags(transitionedFile.with_suffix(".xmp"), [tag.value for tag in tags_gps_all])[
            0
        ]  # -n formats the gps output as decimal numbers
        print(tags)
        assert tags[MowTag.gps_latitude.value] == 20
        assert tags[MowTag.gps_longitude.value] == 10
        assert tags[MowTag.gps_elevation.value] == 2000


def test_image_made_after_last_gps_entry_but_too_small_tolerance_does_not_transition():
    image = "2022-01-01@101025.JPG"
    prepareTest(image_name=image)
    untransitionedFile = join(src, "subsubfolder", image)
    transitionedFile = join(dst, "subsubfolder", image)

    perform_transition(gps_time_tolerance=datetime.timedelta(seconds=2))

    assert exists(untransitionedFile)
    assert not exists(transitionedFile)


# %%
# import folium

# map = folium.Map(location=[15, 0], zoom_start=5)
# folium.Marker([15, 0], popup="Transitioned Image", tooltip="TEST").add_to(map)
# map.save("map.html")

# %%
