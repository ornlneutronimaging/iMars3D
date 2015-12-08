#!/usr/bin/env python

import numpy as np, pylab

# create an image with outliers
from iVenus import sim
img = sim.randomBG(100, 120, 100, 10);
sim.addRandomOutliers(img, 100, 1000, 10)

#
from iVenus import filters
threshold = 450
filters.remove_outliers_bymedian(img, img > threshold)

pylab.imshow(img)
pylab.colorbar()
pylab.show()
