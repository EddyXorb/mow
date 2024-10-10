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

    def __init__(
        self,
        input: TransitionerInput,
    ):

        super().__init__(input)

    def getTasks(self) -> list[TransitionTask]:
        return [TransitionTask(index=index) for index, _ in enumerate(self.toTreat)]


class PassthroughConverter(MediaConverter):
    """
    This is only a decorator for the MediaConverter, as per default the mediaconverter is a passthrough converter.
    """

    def __init__(self, input: TransitionerInput, valid_extensions: list[str] = []):
        input.mediaFileFactory = lambda path: MediaFile(
            path, validExtensions=valid_extensions
        )
        super().__init__(input)
