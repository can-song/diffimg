import rasterio as rio
class_names = None
palette = None
def load(fn, **kwargs):
    with rio.open(fn) as ds:
        data = ds.read()
    return data.transpose(1, 2, 0).squeeze()