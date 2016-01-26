#!/usr/bin/env python

import numpy as np
from smooth import smooth
import pylab

# 
hist0 = np.load("anglespectrum0.npy")
hist180 = np.load("anglespectrum180.npy")
hist0 = smooth(hist0)
hist180 = smooth(hist180)

# fft 
iq0 = np.fft.fft(hist0)
iq180 = np.fft.fft(hist180)
corr = iq0 * np.conjugate(iq180)
corr /= np.abs(corr)
r = np.fft.ifft(corr)

# pylab.imshow(data0)

# pylab.plot(data0[row])
# pylab.plot(data180[row][::-1])
# pylab.plot(data0[:, 0], data180[:, 0])
# pylab.plot(data0[row], data180[row])

# pylab.imshow(angles)

pylab.plot(hist0)
pylab.plot(hist180)
# pylab.plot(smooth(hist0))
# pylab.plot(smooth(hist180))
# pylab.plot(iq0.real)
# pylab.plot(iq180.real)
# pylab.plot(phase)
# pylab.plot(freq)
pylab.plot(r)

# pylab.imshow(np.log(np.abs(F0)+1))
# pylab.imshow(np.log(np.abs(F180))+1)
# pylab.colorbar()
# pylab.clim(0, 20)
pylab.show()
