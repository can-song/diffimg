from PIL import Image
import numpy as np
import rasterio as rio
import pyproj
from pyproj import _delvewheel_init_patch_0_0_25

x = np.zeros((256, 256), dtype=np.uint8)
pil = Image.fromarray(x)
pil.putpalette([255, 0, 0])
pil.save('test.png')

with rio.open('test.png') as ds:
    data = ds.read()
    cmap = ds.colormap(1)
    ...

with rio.open('test.png', 'w') as ds:
    ds.write(data)