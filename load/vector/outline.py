import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
class_names = ['background', 'road']
palette = [[0, 0, 0, 0], [255, 0, 0, 255]]
def load(fn, shape, crs, transform, **kwargs):
    gdf = gpd.read_file(fn)
    gdf = gdf[gdf.class_name=="道路"]
    gdf = gdf.to_crs(crs)
    geometry = gdf.affine_transform((~transform).to_shapely())
    shapes = geometry.boundary.values
    return rasterize(shapes, shape, fill=0, default_value=1, dtype=np.uint8)