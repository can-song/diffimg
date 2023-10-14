import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
# class_names = ['background', 'road']
palette = [[0, 0, 0, 0], [255, 0, 0, 255]]
def load(fn, shape, **kwargs):
    gdf = gpd.read_file(fn)
    shapes = gdf.geometry.values
    # shapes = gdf.geometry.boundary.values
    return rasterize(shapes, shape, fill=0, default_value=1, dtype=np.uint8)