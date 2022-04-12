#!/usr/bin/env python

import os
from imars3d.io import ImageFile

datadir = "../../iMars3D_large_dataset"
f0 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120618_TURBINECT_0180_0_000_0000.fits"))
# f0 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120618_TURBINECT_0180_0_850_0001.fits"))
f180 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120619_TURBINECT_0180_180_200_0212.fits"))
# f180 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120619_TURBINECT_0180_181_050_0213.fits"))
