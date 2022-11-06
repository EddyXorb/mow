import yaml
from general.tkinterhelper import getInputDir
from os import path


class Mow:
    """
    Stands for "M(edia) (fl)OW" - a design to structure your media workflow, be it photos, videos or audio data.
    """

    def __init__(self, settingsfile: str):
        self.settingsfile = settingsfile
        self.settings = self._readsettings()

    def _readsettings(self) -> str:
        if not path.exists(self.settingsfile):
            workingdir = getInputDir("Specify working directory!")
            with open(self.settingsfile, "w") as f:
                yaml.safe_dump({"workingdir": workingdir}, f)

        with open(self.settingsfile, "r") as f:
            return yaml.safe_load(f)

    def copy(self):
        pass

    def rename(self):
        pass

    def group(self):
        pass

    def rate(self):
        pass

    def tag(self):
        pass

    def localize(self):
        pass

    def aggregate(self):
        pass


if __name__ == "__main__":
    Mow(".mowsettings.yml").rename()
