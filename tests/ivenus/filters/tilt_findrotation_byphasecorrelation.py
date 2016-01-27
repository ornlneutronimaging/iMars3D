#!/usr/bin/env python

import numpy as np
from smooth import smooth
import pylab
from scipy.optimize import curve_fit

# 
hist0 = np.load("anglespectrum0.npy")
hist180 = np.load("anglespectrum180.npy")
hist0 = smooth(hist0)[:hist0.size]
hist180 = smooth(hist180)[:hist180.size]

# fft 
iq0 = np.fft.fft(hist0)
iq180 = np.fft.fft(hist180)
# corr = iq0 * np.conjugate(iq180)
corr = iq180 * np.conjugate(iq0)
corr /= np.abs(corr)
r = np.fft.ifft(corr)
#
r = np.real(r)

# the argmax of r should be what we want.
# - only data within a few degrees are useful
r[10:350] = 0
index = np.argmax(r[1:]) + 1
width = 2
peak = r[index-width : index+width+1]
def poly2(x, *p):
    a0, a1, a2 = p
    return a0-a1*(x-a2)**2

p0 = [r[index], 1., width]
x = np.arange(peak.size)
# import pdb; pdb.set_trace()
coeff0, var_matrix = curve_fit(poly2, x, peak, p0=p0)
print coeff0
peak_fit = poly2(x, *coeff0)
# npylab.plot(x, peak)
# pylab.plot(x, peak_fit)
print coeff0[-1] - width + index

# pylab.plot(hist0)
# pylab.plot(hist180)
# pylab.plot(smooth(hist0))
# pylab.plot(smooth(hist180))
# pylab.plot(iq0.real)
# pylab.plot(iq180.real)
# pylab.plot(phase)
# pylab.plot(freq)
pylab.plot(r)

pylab.show()
