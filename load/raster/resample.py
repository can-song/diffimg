import rasterio as rio
from rasterio.enums import Resampling
class_names = None
palette = None
def load(fn, shape, **kwargs):
    width, height = shape
    with rio.open(fn) as ds:
        data = ds.read(out_shape=(ds.count, height, width),
                       resampling=Resampling.nearest)
    return data.transpose(1, 2, 0).squeeze()