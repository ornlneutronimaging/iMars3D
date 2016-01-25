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


def fft_angles_and_intensities(image):
    """read image and create the angles and intensities
    in the frequency domain for the image.
    """
    F = np.fft.fft2(image)
    # clean up borders
    F[0,:] = 0; F[:, 0] = 0
    F[-1,:] = 0; F[:, -1] = 0
    # shift origin to the center of the freq-domain image
    F = np.fft.fftshift(F)
    # calculate angles
    sizey, sizex = F.shape
    x = np.arange(0, sizex, 1.) - sizex//2
    xx = np.tile(x, sizey).reshape(F.shape)
    y = np.arange(0, sizey, 1.) - sizey//2
    yy = np.repeat(y, sizex).reshape(F.shape)
    angles = np.arctan2(yy, xx)
    return angles, np.abs(F)


import numpy

def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=numpy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=numpy.ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='valid')
    return y


    
import pylab
row = 100
for row in range(10, 1000, 100):
    # pylab.plot(data0[:, row])
    # pylab.show()
    continue

bins = 360

angles0,F0 = fft_angles_and_intensities(data0)
hist0, edges0 = np.histogram(angles0, weights=F0, bins=bins)

angles180,F180 = fft_angles_and_intensities(data180)
hist180, edges180 = np.histogram(angles180, weights=F180, bins=bins)

# pylab.imshow(data0)
data0int = np.array(1.*data0/np.max(data0)*255, dtype="uint8")
import cv2
edges = cv2.Canny(data0int, 25, 50)
# pylab.imshow(data0int)
pylab.imshow(edges, cmap="gray")

# pylab.plot(data0[row])
# pylab.plot(data180[row][::-1])
# pylab.plot(data0[:, 0], data180[:, 0])
# pylab.plot(data0[row], data180[row])

# pylab.plot(smooth(hist0))
# pylab.plot(smooth(hist180))

# pylab.imshow(angles)

# pylab.imshow(np.log(np.abs(F0)+1))
# pylab.imshow(np.log(np.abs(F180))+1)
pylab.colorbar()
# pylab.clim(0, 20)
pylab.show()
