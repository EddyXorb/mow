import os
import shutil
from ..general.mediatransitioner import TransitionerInput
from ..general.mediaconverter import MediaConverter
from .imagefile import ImageFile
from subprocess import check_output
from exiftool import ExifTool
from PIL import Image, ImageOps

# The Adobe DNG Converter supports the following command line options:
# -c Output lossless compressed DNG files (default).
# -u Output uncompressed DNG files.
# -l Output linear DNG files.
# -e Embed original raw file inside DNG files.
# -p0 Set JPEG preview size to none.
# -p1 Set JPEG preview size to medium size (default).
# -p2 Set JPEG preview size to full size.
# -fl Embed fast load data inside DNG files.
# -lossy Use lossy compression.
# -side <num> Limit size to <num> pixels/side.
# -count <num> Limit pixel count to <num> pixels/image.
# -cr2.4 Set Camera Raw compatibility to 2.4 and later
# -cr4.1 Set Camera Raw compatibility to 4.1 and later
# -cr4.6 Set Camera Raw compatibility to 4.6 and later
# -cr5.4 Set Camera Raw compatibility to 5.4 and later
# -cr6.6 Set Camera Raw compatibility to 6.6 and later
# -cr7.1 Set Camera Raw compatibility to 7.1 and later
# -cr11.2 Set Camera Raw compatibility to 11.2 and later
# -cr12.4 Set Camera Raw compatibility to 12.4 and later
# -cr13.2 Set Camera Raw compatibility to 13.2 and later
# -cr14.0 Set Camera Raw compatibility to 14.0 and later
# -cr15.3 Set Camera Raw compatibility to 15.3 and later
# -dng1.1 Set DNG backward version to 1.1
# -dng1.3 Set DNG backward version to 1.3
# -dng1.4 Set DNG backward version to 1.4
# -dng1.5 Set DNG backward version to 1.5
# -dng1.6 Set DNG backward version to 1.6
# -dng1.7 Set DNG backward version to 1.7
# -dng1.7.1 Set DNG backward version to 1.7.1
# -jxl Use JPEG XL compression, if supported by image type. Implies -dng1.7
# -jxl_distance Set JPEG XL distance metric (see libjxl documentation). Valid values are 0.0 to 6.0. 0.0 is lossless and 0.1 is very high-quality lossy Implies -jxl
# -jxl_effort Set JPEG XL effort level (see libjxl documentation). Valid values are 1 to 9, where 1 = fastest. Implies -jxl
# -losslessJXL Uses Lossless JPEG XL compression. Implies -jxl and -jxl_distance 0.0 and -jxl_effort 7
# -lossyMosaicJXL Uses Lossy JPEG XL compression with Bayer images.
# -mp Process multiple raw files in parallel. Default is sequential (one image at a time).
# -d <directory> Output converted files to the specified directory. Default is the same directory as the input file.
# -o <filename> Specify the name of the output DNG file. Default is the name of the input file with the extension changed to “.dng”.

DESIRED_RAW_PREVIEW_SIZE = (3200, 2400)
DNG_PREVIEW_IMAGE_QUALITY = 25


def convertImage(
    source: ImageFile, target_dir: str, settings: dict[str, str]
) -> ImageFile | None:
    """
    The converter does have to not create missing directories. This is done by the Transitioner.
    If there is a raw file, will convert this to dng with optimized preview image
    (smaller in size, but bigger in resolution).
    """
    new_jpgfile_location = None
    new_dngfile_location = None

    jpgfile = source.getJpg()

    if jpgfile is not None:
        shutil.move(jpgfile, target_dir)
        new_jpgfile_location = os.path.join(target_dir, os.path.basename(jpgfile))
        extension_to_remove = os.path.splitext(jpgfile)[1]
        source.remove_extension(extension_to_remove)

    rawfile = source.getRaw()

    if rawfile is not None:
        if rawfile.endswith(".dng") or rawfile.endswith(".DNG"):
            shutil.move(rawfile, target_dir)
            new_dngfile_location = os.path.join(target_dir, os.path.basename(rawfile))
            source.remove_extension(os.path.splitext(rawfile)[1])
        else:
            new_dngfile_location = convert_to_dng(target_dir, settings, rawfile)
            resize_preview_image_of_dng(new_dngfile_location)

    if new_jpgfile_location is not None:
        return ImageFile(new_jpgfile_location)
    if new_dngfile_location is not None:
        return ImageFile(new_dngfile_location)

    return None


def convert_to_dng(target_dir, settings, rawfile):
    check_output(
        [
            settings["dng_converter_exe"],
            "-cr11.2",
            "-p2",
            "-d",
            target_dir,
            rawfile,
        ]
    )

    new_rawfile_location = os.path.join(
        target_dir, os.path.splitext(os.path.basename(rawfile))[0] + ".dng"
    )

    return new_rawfile_location


def resize_preview_image_of_dng(dng_file_path: str):
    """
    This function resizes the preview image of a dng file to a smaller size, but bigger resolution. It is strange, but the dng converter does not offer more options than "1024-768"
    and "full-size" preview images, where the small preview is really too small to be visualized in image viewers and the big takes too much space extra (> 3 mb). Using this function,
    the preview image is resized to a big enough size, and lower quality, which is a good compromise between size and quality (typically 300 kb for a 20 MP image).
    """
    temporary_preview_image_path = dng_file_path.replace(
        ".dng", "_preview_deleteme.jpg"
    )

    with ExifTool() as et:
        # 1. extract current preview image from dng
        et.execute(
            f"-preview:jpgfromraw",
            "-b",
            "-W",
            temporary_preview_image_path,
            dng_file_path,
        )
        # 2. resize preview image
        ImageOps.contain(
            Image.open(temporary_preview_image_path), size=DESIRED_RAW_PREVIEW_SIZE
        ).save(temporary_preview_image_path, quality=DNG_PREVIEW_IMAGE_QUALITY)
        # 3. remove all existing preview images from dng
        et.execute(
            "-preview:previewimage=", "-P", "-overwrite_original", dng_file_path
        )
        # 4. set resized preview image in dng
        et.execute(
            f"-preview:jpgfromraw<={temporary_preview_image_path}",
            "-P",
            "-overwrite_original",
            dng_file_path,
        )

    if os.path.exists(
        temporary_preview_image_path
    ):  # maybe something went wrong and the file was not created
        os.remove(temporary_preview_image_path)


class ImageConverter(MediaConverter):
    """
    Pasthrough for jpg, conversion to dng for raw files.

        Note: when importing the converted dng files into lightroom, make sure to set the profile to "Adobe Standard" to get the best results.
        The dng file has in its xmp metadata another profile as  suggestion named "Camera Natural" which is chosen by default. This profile is not as good as "Adobe Standard".
    """

    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = ImageFile
        input.converter = convertImage
        input.rewriteMetaTagsOnConverted = (
            False  # TODO check if dng contains all info needed
        )
        input.nr_processes_for_conversion = max(1, int(os.cpu_count() * 0.7))
        super().__init__(input)

        if "dng_converter_exe" not in input.settings:
            raise Exception("dng_converter_exe not set in settings!")
