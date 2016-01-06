#!/usr/bin/env python

import numpy as np, pylab
from ivenus import filters, io

# test data
import os
dir = os.path.dirname(__file__)
path = os.path.join(dir, "..", "..", "iVenus_data_set", "20120618_TURBINECT_0180_46_750_0055.fits")
img = io.ImageFile(path).getData()

# filter
print np.max(img)
img = filters.gamma_filtering.filter(img)
print np.max(img)

# display
pylab.imshow(img)
pylab.colorbar()
pylab.show()
