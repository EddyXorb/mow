# affinity propagation clustering
#%%
from numpy import unique
from numpy import where
from sklearn.datasets import make_classification
from sklearn.cluster import AffinityPropagation
from matplotlib import pyplot
import os
import datetime as dt

from PIL import Image, ExifTags

#%%
testfile = "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\\2021\\_noch_einsortieren\\P9032695.JPG"

def getExifDateFrom(file : str) -> dt.datetime:
    img = Image.open(testfile)
    img_exif = img.getexif()

    if img_exif is None:
        raise Exception('Sorry, image has no exif data: ', testfile)
    else:
        date = img_exif[306]
        return dt.datetime.strptime(date, '%Y:%m:%d %H:%M:%S')


def getNewImageFileNameFor(file : str) -> str:
    date = getExifDateFrom(file)
    prefixDate = f"{date:%Y-%m-%d.T.%H.%M.%S}"
    return os.path.join(os.path.dirname(file),prefixDate + "_" + os.path.basename(file))
    
print(getNewImageFileNameFor(testfile))
#%%

#%%
# define dataset
X, _ = make_classification(n_samples=1000, n_features=1, n_informative=1, n_redundant=0, n_clusters_per_class=1, random_state=4)

folder = "C:\\Users\\claud\\Nextcloud\\Photos\\Fotos\2021\\_noch_einsortieren"
fileToTimestamp = {}

for root, dirs, files in os.walk(folder):
    for f in files:
        file = os.path.join(root,f)
        

# define the model
#%%
model = AffinityPropagation(damping=0.9,random_state = None)
# fit the model
model.fit(X)
# assign a cluster to each example
yhat = model.predict(X)
# retrieve unique clusters
clusters = unique(yhat)
# create scatter plot for samples from each cluster
for cluster in clusters:
	# get row indexes for samples with this cluster
	row_ix = where(yhat == cluster)
	# create scatter of these samples
	pyplot.scatter(X[row_ix, 0],X[row_ix, 0])

# show the plot
pyplot.show()
# %%
