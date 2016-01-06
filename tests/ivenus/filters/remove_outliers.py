#!/usr/bin/env python

import numpy as np, pylab
from ivenus import filters

# create an image with outliers
from ivenus import sim
img = sim.randomBG(100, 120, 100, 10);
sim.addRandomOutliers(img, 100, 1000, 10)

# filter
threshold = 450
filters.gamma_filtering.remove_outliers_bymedian(img, img>threshold)

# display
pylab.imshow(img)
pylab.colorbar()
pylab.show()
