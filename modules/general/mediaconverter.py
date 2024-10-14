import multiprocessing
import os
from typing import Callable

from tqdm import tqdm

from ..mow.mowtags import MowTags
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

        try:
            convertedFile = converter(toTransition, os.path.dirname(newPath), settings)
        except Exception as e:
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
                tqdm(convertedFiles) if self.verbosityLevel >= 3 else convertedFiles
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

        xmptagstowrite = self.et.get_tags(str(toTransition), MowTags.all)[0]
        xmptagstowrite.pop("SourceFile")
        self.et.set_tags(
            convertedFile.getAllFileNames(),
            xmptagstowrite,
            params=["-P", "-overwrite_original", "-L", "-m"],
        )


class PassthroughConverter(MediaConverter):
    """
    This is only a decorator for the MediaConverter, as per default the mediaconverter is a passthrough converter.
    """

    def __init__(self, input: TransitionerInput, valid_extensions: list[str] = []):
        input.mediaFileFactory = lambda path: MediaFile(
            path, validExtensions=valid_extensions
        )
        super().__init__(input)
