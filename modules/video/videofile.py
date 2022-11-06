from ..general.mediafile import MediaFile


class VideoFile(MediaFile):
    supportedVideoFileEndings = [".MOV", ".mp4", ".3gp"]

    def __init__(self, path: str):
        super().__init__(path, validExtensions=self.supportedVideoFileEndings)
