import multiprocessing
import os
import shutil
from typing import Callable
from rich.progress import track

from ..mow.mowtags import tags_all, MowTag
from ..general.mediafile import MediaFile
from ..general.mediatransitioner import (
    MediaTransitioner,
    TransitionerInput,
    TransitionTask,
)


class MediaConverter(MediaTransitioner):
    """
    converter: Convert mediafile and put result into directory given with second argument
    """

    @staticmethod
    def converter_wrapper(
        toTransition: MediaFile,
        newPath: str,
        task_index: int,
        converter,
        settings: dict[str, str],
    ) -> tuple[MediaFile, MediaFile | None, int]:

        os.makedirs(os.path.dirname(newPath), exist_ok=True)

        sidecar_present = toTransition.has_sidecar()

        if sidecar_present:
            shutil.move(toTransition.get_sidecar(), os.path.dirname(newPath))
            toTransition.extensions.remove(".xmp")

        try:
            convertedFile = converter(toTransition, os.path.dirname(newPath), settings)
            if sidecar_present and not convertedFile.has_sidecar():
                convertedFile.extensions.append(".xmp")

        except Exception:
            return toTransition, None, task_index

        for file in convertedFile.getAllFileNames():
            if not os.path.exists(file):
                return toTransition, None

        return toTransition, convertedFile, task_index

    def __init__(
        self,
        input: TransitionerInput,
    ):
        super().__init__(input)

    def getTasks(self) -> list[TransitionTask]:
        return [TransitionTask(index=index) for index, _ in enumerate(self.toTreat)]

    def doConversionOf(self, tasks: list[TransitionTask]):
        convertedFiles: list[tuple[MediaFile, MediaFile]] = []

        conversion_tasks = self.get_conversion_tasks(tasks)
        results = self.get_conversion_results(conversion_tasks)

        for toTransition, convertedFile, task_index in results:
            if convertedFile is None:
                tasks[task_index].skip = True
                tasks[task_index].skipReason = "Conversion failed"
                continue

            convertedFiles.append((toTransition, convertedFile))

            self.print_debug(
                self.getTransitionInfoString(
                    toTransition=toTransition,
                    newName=(convertedFile.getDescriptiveBasenames()),
                ),
            )

        self.print_info(
            f"Finished conversion of {len(tasks)} mediafiles of which {len([file[1] for file in convertedFiles if file[1] is not None])} were successful."
        )

        if self.rewriteMetaTagsOnConverted:
            self.print_info("Rewrite meta file tags on converted..")
            for toTransition, convertedFile in (
                track(convertedFiles) if self.verbosityLevel >= 3 else convertedFiles
            ):
                self.performMetaTagRewriteOf(toTransition, convertedFile)

        self.print_info("Delete original files..")
        for toTransition, convertedFile in convertedFiles:
            if not toTransition.empty() and not self.dry:
                self.deleteMediaFile(toTransition)

    def get_conversion_results(
        self, conversion_tasks
    ) -> list[tuple[MediaFile, MediaFile, int]]:
        if self.dry:
            results = [
                (toTransition, toTransition, index)
                for toTransition, _, index, _, _ in conversion_tasks
            ]
        else:
            if self.nr_processes_for_conversion != 1:
                self.print_info(
                    f"Using {self.nr_processes_for_conversion} processes for conversion.."
                )
                with multiprocessing.Pool(
                    processes=self.nr_processes_for_conversion
                ) as pool:
                    results = pool.starmap(self.converter_wrapper, conversion_tasks)
            else:
                results = [self.converter_wrapper(*task) for task in conversion_tasks]

        return results

    def get_conversion_tasks(
        self, tasks
    ) -> list[tuple[MediaFile, str, int, Callable, dict[str, str]]]:
        conversion_tasks = []
        for index, task in enumerate(tasks):
            toTransition = self.toTreat[task.index]
            newPath = self.getNewNameFor(task)
            conversion_tasks.append(
                (toTransition, newPath, index, self.converter, self.settings)
            )

        return conversion_tasks

    def performMetaTagRewriteOf(
        self, toTransition: MediaFile, convertedFile: MediaFile
    ):
        if self.dry:
            return
        if self.writeMetaTagsToSidecar:
            xmptagstowrite = self.fm.read_from_sidecar(str(toTransition), tags_all)
            xmptagstowrite.pop(MowTag.sourcefile)
            self.fm.write_tags(str(convertedFile), xmptagstowrite)
        else:
            xmptagstowrite = self.fm.read_tags(str(toTransition.getAllFileNames()[0]), tags_all)
            xmptagstowrite.pop(MowTag.sourcefile)
            for file in convertedFile.getAllFileNames():
                self.fm.write_tags(str(file), xmptagstowrite)


class PassthroughConverter(MediaConverter):
    """
    This is only a decorator for the MediaConverter, as per default the mediaconverter is a passthrough converter.
    """

    def __init__(self, input: TransitionerInput, valid_extensions: list[str] = []):
        input.mediaFileFactory = lambda path: MediaFile(
            path, validExtensions=valid_extensions
        )
        input.writeMetaTagsToSidecar = False
        super().__init__(input)
