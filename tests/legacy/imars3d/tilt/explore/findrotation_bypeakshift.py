#!/usr/bin/env python

import numpy as np
from smooth import smooth
import pylab

#
hist0 = np.load("anglespectrum0.npy")
hist180 = np.load("anglespectrum180.npy")

hist0 = smooth(hist0)
hist180 = smooth(hist180)

pylab.plot(hist0)
pylab.plot(hist180)
pylab.show()

# find the maximum between 0 and 180
i0 = np.argmax(hist0[:180])
i180 = np.argmax(hist180[:180])
print(i0, i180)

width = 3
pk0 = hist0[i0 - width : i0 + width]
pk180 = hist180[i180 - width : i180 + width]


from scipy.optimize import curve_fit


def gauss(x, *p):
    A, mu, sigma = p
    return A * np.exp(-((x - mu) ** 2) / (2.0 * sigma ** 2))


def poly2(x, *p):
    a0, a1, a2 = p
    return a0 - a1 * (x - a2) ** 2


# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
# p0 = [hist0[i0], 0, 5.]
p0 = [hist0[i0], 1.0, width]
x = np.arange(width * 2)
# coeff0, var_matrix = curve_fit(gauss, x, pk0, p0=p0)
coeff0, var_matrix = curve_fit(poly2, x, pk0, p0=p0)
print(coeff0)
# hist0_fit = gauss(x, *coeff0)
hist0_fit = poly2(x, *coeff0)
pylab.plot(x, pk0)
pylab.plot(x, hist0_fit)

# coeff180, var_matrix = curve_fit(gauss, x, pk180, p0=p0)
coeff180, var_matrix = curve_fit(poly2, x, pk180, p0=p0)
print(coeff180)
hist180_fit = poly2(x, *coeff180)


print(i180 + coeff180[-1] - (i0 + coeff0[-1]))

# pylab.plot(x, pk180)
# pylab.plot(x, hist180_fit)
