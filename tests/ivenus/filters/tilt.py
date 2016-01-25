#!/usr/bin/env python

import os, numpy as np
from ivenus.io import ImageFile

datadir = "../../iVenus_large_dataset"
f0 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120618_TURBINECT_0180_0_000_0000.fits"))
f180 = ImageFile(os.path.join(datadir, "reconstruction", "turbine", "20120619_TURBINECT_0180_180_200_0212.fits"))


data0 = f0.getData()
print data0.shape
data180 = f180.getData()

# flip horizontally
data180 = np.fliplr(data180)

F0 = np.fft.fft2(data0)
F180 = np.fft.fft2(data180)
# clean up borders
F0[0,:] = 0; F0[:, 0] = 0
F0[-1,:] = 0; F0[:, -1] = 0
F180[0,:] = 0; F180[:, 0] = 0
F180[-1,:] = 0; F180[:, -1] = 0

F0 = np.fft.fftshift(F0)
F180 = np.fft.fftshift(F180)

import pylab
row = 100
for row in range(10, 1000, 100):
    # pylab.plot(data0[:, row])
    # pylab.show()
    continue
# pylab.imshow(data0)
# pylab.plot(data0[row])
# pylab.plot(data180[row][::-1])
# pylab.plot(data0[:, 0], data180[:, 0])
# pylab.plot(data0[row], data180[row])

pylab.imshow(np.log(np.abs(F0)+1))
# pylab.imshow(np.log(np.abs(F180))+1)
pylab.clim(0, 20)
pylab.colorbar()
pylab.show()
