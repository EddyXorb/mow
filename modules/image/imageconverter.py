import os
import shutil
from ..general.mediatransitioner import TransitionerInput
from ..general.mediaconverter import MediaConverter
from .imagefile import ImageFile
from subprocess import check_output

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


def convertImage(
    source: ImageFile, target_dir: str, settings: dict[str, str]
) -> ImageFile | None:
    """
    The converter does have to not create missing directories. This is done by the Transitioner.
    """
    new_jpgfile_location = None
    new_rawfile_location = None

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
            new_rawfile_location = os.path.join(target_dir, os.path.basename(rawfile))
            source.remove_extension(os.path.splitext(rawfile)[1])
        else:
            check_output(
                [settings["dng_converter_exe"], "-cr11.2", "-d", target_dir, rawfile]
            )

            new_rawfile_location = os.path.join(
                target_dir, os.path.splitext(os.path.basename(rawfile))[0] + ".dng"
            )

    if new_jpgfile_location is not None:
        return ImageFile(new_jpgfile_location)
    if new_rawfile_location is not None:
        return ImageFile(new_rawfile_location)

    return None


class ImageConverter(MediaConverter):
    def __init__(self, input: TransitionerInput):
        input.mediaFileFactory = ImageFile
        input.converter = convertImage
        input.rewriteMetaTagsOnConverted = (
            False  # TODO check if dng contains all info needed
        )
        input.use_multiprocessing_for_conversion = True
        super().__init__(input)
