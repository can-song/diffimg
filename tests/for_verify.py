# from PIL import Image

# img = Image.open('test.png')
# img = img.convert('RGBA')
# img.save('tests/test.png')


# t = 57.4
# c = 18.41



# t = 51.52
# c = 21.97

# t /= 100
# c /= 100

# def func(t, c):
#     return 5 * (t * c) / (4 * c + t)

# print(func(t, c))


import numpy as np
a = np.arange(4).reshape(2, -1)
print(a)
a[...] = 0
print(a)