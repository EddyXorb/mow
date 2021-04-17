import os
import datetime as dt
import numpy as np

from imagehelper import getExifDateFrom

#%%
testfile = "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\images\\2020-07-06.T.17.13.41_P7062069.JPG"
folder = (
    "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\images\\"
)
targetfolder = os.path.join(folder,"clustered")
files = os.listdir(folder)