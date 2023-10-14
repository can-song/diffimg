import rasterio as rio
from skimage.morphology import skeletonize
import numpy as np
class_names = None
palette = [[0, 0, 0, 0], [255, 0, 0, 255]]
def load(fn, **kwargs):
    with rio.open(fn) as ds:
        data = ds.read()
    return skeletonize(data[0] >= 128).astype(np.uint8)