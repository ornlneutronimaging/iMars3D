#!/usr/bin/env python

"""
In this script we are trying compute the tilt angle of the
rotation axis.

We use a pair of images that are 180 degrees away from each
other.
They are supposed to be exact mirror images, but not
because of the tilt.
The rotation angle from the master image and the
mirrored slave image divided by 2 is the tilt angle.
So the main thing here we need to find that rotation angle.

The rotation angle can be estimated from looking at the image
and derive from rotation of a line (or any shape).
This can be achieved by selecting a point with distinctive
feature.
This can be done by hand:
* selected two points on the edge of the base
* their coordinates in 0 and 180.200 degrees are
  - 278,590;  1862,524
  - 298,548;  1874,570
* computed the rotation angle (using np.arctan2)
  to be -3.2 degrees (positive is counterclockwise if looking upon the image)

So this will be the ground truth when we test our algorithm.

"""


import os, numpy as np
from scipy import ndimage
import pylab
from smooth import smooth

from inputimages import f0, f180

border = 5
rotation = 30.0  # 45.
data0 = f0.getData()
data0 = ndimage.rotate(data0, rotation)
sizeY, sizeX = data0.shape
data0 = data0[sizeY // 4 : sizeY * 3 // 4, sizeX // 4 : sizeX * 3 // 4]
print(data0.shape)
# pylab.imshow(data0)

data180 = f180.getData()
# flip horizontally
data180 = np.fliplr(data180)
data180 = ndimage.rotate(data180, rotation)
sizeY, sizeX = data180.shape
data180 = data180[sizeY // 4 : sizeY * 3 // 4, sizeX // 4 : sizeX * 3 // 4]


def find_edges(data):
    dataint = np.array(1.0 * data / np.max(data) * 255, dtype="uint8")
    import cv2

    edges = cv2.Canny(dataint, 25, 50)
    # pylab.imshow(dataint)
    # pylab.imshow(edges, cmap="gray")
    return edges


def fft_angles_and_intensities(image):
    """read image and create the angles and intensities
    in the frequency domain for the image.
    """
    F = np.fft.fft2(image)
    # clean up borders
    F[0:border, :] = 0
    F[:, 0:border] = 0
    F[-border:] = 0
    F[:, -border:] = 0
    # shift origin to the center of the freq-domain image
    F = np.fft.fftshift(F)
    # calculate angles
    sizey, sizex = F.shape
    x = np.arange(0, sizex, 1.0) - sizex // 2
    xx = np.tile(x, sizey).reshape(F.shape)
    y = np.arange(0, sizey, 1.0) - sizey // 2
    yy = np.repeat(y, sizex).reshape(F.shape)
    rho = (xx * xx + yy * yy) ** 0.5
    angles = np.arctan2(yy, xx)

    R = min(image.shape) // 2
    bracket = (rho > 0.1 * R) * (rho < R)
    # return angles, np.abs(F)
    return angles[bracket], np.abs(F[bracket])


row = 100
for row in range(10, 1000, 100):
    # pylab.plot(data0[:, row])
    # pylab.show()
    continue

bins = 360

# angles0,F0 = fft_angles_and_intensities(find_edges(data0))
angles0, F0 = fft_angles_and_intensities(data0)
hist0, edges0 = np.histogram(angles0, weights=F0, bins=bins)

# angles180,F180 = fft_angles_and_intensities(find_edges(data180))
angles180, F180 = fft_angles_and_intensities(data180)
hist180, edges180 = np.histogram(angles180, weights=F180, bins=bins)

# import pdb; pdb.set_trace()
#
np.save("anglespectrum0.npy", hist0)
np.save("anglespectrum180.npy", hist180)

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

# pylab.imshow(np.log(np.abs(F0)+1))
# pylab.imshow(np.log(np.abs(F180))+1)
# pylab.colorbar()
# pylab.clim(0, 20)
pylab.show()
