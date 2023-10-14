import rasterio as rio
from skimage.morphology import skeletonize
from skimage.segmentation import find_boundaries
import numpy as np
class_names = None
palette = [[0, 0, 0, 0], [255, 0, 0, 255]]
def load(fn, **kwargs):
    with rio.open(fn) as ds:
        data = ds.read()
    data = data.squeeze()
    if data.ndim == 3:
        data = np.left_shift(data[0], 16) + \
            np.left_shift(data[1], 8) + \
            data[2]
    return find_boundaries(data)