from dataclasses import dataclass
from .mediatransitioner import MediaTransitioner, TansitionerInput


@dataclass(kw_only=True)
class GrouperInput(TansitionerInput):
    interactive = False
    separationDistanceInHours = 12

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MediaGrouper(MediaTransitioner):
    def __init__(self, input: GrouperInput):
        super().__init__(input)
        self.interactive = input.interactive
        self.separationDistanceInHours = input.separationDistanceInHours
