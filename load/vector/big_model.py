import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
class_names = ['未分类', '耕地','建筑','道路','水体','云','植被','温室大棚',
               '建筑工地','露天采掘场','露天体育场','河流','水渠',
               '湖泊','库塘','园地','林地','草地','光伏','地表光伏','屋顶光伏',
               '']
palette = np.random.randint(64, 256, (256, 4))
palette[0] = 0
palette[len(class_names)-1] = 255
palette[:, -1] = 255

def load(fn, shape, crs, transform, **kwargs):
    gdf = gpd.read_file(fn)
    gdf = gdf.to_crs(crs)
    geometry = gdf.affine_transform((~transform).to_shapely())
    shapes = zip(geometry.values, gdf.class_name.apply(
        lambda x: class_names.index(x) if class_names.count(x) else len(class_names)).values)
    return rasterize(shapes, shape, fill=0, default_value=255, dtype=np.uint8)