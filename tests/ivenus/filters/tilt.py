#!/usr/bin/env python

import os
from ivenus.io import ImageFile

datadir = "../../iVenus_large_dataset"
f0 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120618_TURBINECT_0180_0_000_0000.fits"))
f180 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120619_TURBINECT_0180_180_200_0212.fits"))

data0 = f0.getData()
print data0.shape
data180 = f180.getData()

import pylab
pylab.plot(data0[:, 0], data180[:, 0])
pylab.show()
