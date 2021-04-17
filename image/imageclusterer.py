#%%

import os
import datetime as dt
import numpy as np
from typing import List

from imagehelper import getExifDateFrom
from imagefile import ImageFile


class DateImageFile(ImageFile):
    def __init__(self, file):
        super().__init__(file)
        if self.isValid():
            self.date = getExifDateFrom(self.getJpg())
            self.baseTime: dt.datetime = None


#%%
testfile = "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\images\\2020-07-06.T.17.13.41_P7062069.JPG"
folder = (
    "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\images\\"
)

targetfolder = os.path.join(folder, "clustered")
files = os.listdir(folder)
#%%
datedFiles: List[DateImageFile] = []
for file in files:

    ifile = DateImageFile(os.path.join(folder, file))
    if not ifile.isValid():
        continue

    datedFiles.append(ifile)

#%%
datedFiles.sort(key=lambda x: x.date)
#%%
secondsThreshold = 3600 * 48  # two days
#%%
lastTime = datedFiles[0].date
lastBaseTime = datedFiles[0].date
cntBaseTimes = 0

for im in datedFiles:
    sec = (im.date - lastTime).total_seconds()
    if sec > secondsThreshold:
        lastBaseTime = im.date
        cntBaseTimes += 1

    lastTime = im.date
    im.baseTime = lastBaseTime

print("Nr cluster found: ", cntBaseTimes)

#%%
