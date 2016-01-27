#!/usr/bin/env python

from inputimages import f0, f180
from scipy import ndimage
import numpy as np

rotation = 3.2

data0 = f0.getData()
data0 = ndimage.rotate(data0, rotation)

data180 = f180.getData()
data180 = np.fliplr(data180)

import pylab
# pylab.imshow(data0)
pylab.imshow(data180)
pylab.colorbar()
pylab.show()
