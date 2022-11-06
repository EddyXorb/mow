#%%
from ..general.mediafilerenamer import MediaFileRenamer

from .imagefile import ImageFile
from .imagefile import ImageFile


class ImageRenamer(MediaFileRenamer):
    """
    src : directory which will be search for files
    dst : directory where renamed files should be placed
    recursive : if true, dives into every subdir to look for image files
    move : if true, moves files, else copies them
    restoreOldNames : inverts the renaming logic to simply remove the timestamp prefix.
    maintainFolderStructure: if recursive is true will rename subfolders into subfolders, otherwise all files are put into root repo of dest
    dry: don't actually rename files
    writeXMP: sets XMP-dc:Source to original filename and XMP-dc:date to creationDate
    """

    def __init__(
        self,
        src: str,
        dst: str,
        recursive: bool = True,
        move: bool = False,
        restoreOldNames=False,
        verbose=False,
        maintainFolderStructure=True,
        dry=False,
        writeXMP=False,
    ):
        super().__init__(
            src=src,
            dst=dst,
            mediafilefactory=lambda file: ImageFile(file),
            recursive=recursive,
            move=move,
            restoreOldNames=restoreOldNames,
            verbose=verbose,
            maintainFolderStructure=maintainFolderStructure,
            dry=dry,
            writeXMP=writeXMP,
        )
