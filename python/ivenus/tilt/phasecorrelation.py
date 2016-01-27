#!/usr/bin/env python

import os, numpy as np
from scipy import ndimage
import pylab
from matplotlib import pyplot as plt
from smooth import smooth
from scipy.optimize import curve_fit

class PhaseCorrelation:

    # intensities in freq domain along x,y axes are always high
    # clearn them within the border size
    border = 5
    # see below doc in __call__
    rotation = 30. # 45.
    # this is for collecting I(theta) histogram. 
    # better be integer multiplication of 360
    bins = 360
    logging_dir = "log.tilt-phasecorrelation"
    
    def __call__(self, img0, img180):
        """
        implementation details:
        * the signal lines in the freq domain may overlap with
          x,y axes, where artifacts exist. so we rotate
          the input images by self.rotation
        """
        # 0 degree data
        data0 = img0.getData()
        data0 = ndimage.rotate(data0, self.rotation)
        sizeY, sizeX = data0.shape
        # only take the rectangle region where data exist
        data0 = data0[sizeY//4:sizeY*3//4, sizeX//4:sizeX*3//4]
        # 180 degree data
        # print data0.shape
        data180 = img180.getData()
        # flip horizontally
        data180 = np.fliplr(data180)
        data180 = ndimage.rotate(data180, self.rotation)
        sizeY, sizeX = data180.shape
        data180 = data180[sizeY//4:sizeY*3//4, sizeX//4:sizeX*3//4]
        # create histogram
        angles0,F0 = fft_angles_and_intensities(
            data0, self.border, os.path.join(self.logging_dir, "0"))
        hist0, edges0 = np.histogram(angles0, weights=F0, bins=self.bins)
        angles180,F180 = fft_angles_and_intensities(
            data180, self.border, os.path.join(self.logging_dir, "180"))
        hist180, edges180 = np.histogram(angles180, weights=F180, bins=self.bins)
        # 
        # now that we have the histogram I(theta), we use 
        # phase correlation method to determine the shift
        iq0 = np.fft.fft(hist0)
        iq180 = np.fft.fft(hist180)
        # corr = iq0 * np.conjugate(iq180)
        corr = iq180 * np.conjugate(iq0)
        corr /= np.abs(corr)
        r = np.fft.ifft(corr)
        r = np.real(r)
        # the argmax of r should be what we want.
        # - only data within a few degrees are useful
        r[10:350] = 0
        index = np.argmax(r[1:]) + 1
        # - fit the peak with a polynomial and get the high point
        width = 2
        peak = r[index-width : index+width+1]
        def poly2(x, *p):
            a0, a1, a2 = p
            return a0-a1*(x-a2)**2
        # initial guess for fit
        p0 = [r[index], 1., width]
        # x axis
        x = np.arange(peak.size)
        # import pdb; pdb.set_trace()
        # fit
        coeff0, var_matrix = curve_fit(poly2, x, peak, p0=p0)
        # fitted peak
        peak_fit = poly2(x, *coeff0)
        # plot 
        pylab.figure(figsize=(5, 14))
        # - I(theta) histogram
        axes = plt.subplot(3,1,1)
        pylab.plot(hist0)
        pylab.plot(hist180)
        pylab.xlabel("I(theta)")
        # - phase correlation result
        axes = plt.subplot(3,1,2)
        iaxes = pylab.plot(r)
        pylab.xlabel("Correlation")
        # - peak fitting
        axes = plt.subplot(3,1,3)
        pylab.plot(x, peak)
        pylab.plot(x, peak_fit)
        pylab.xlabel("Peak fitting")
        # - save
        logging_dir = self.logging_dir
        if not os.path.exists(logging_dir):
            os.makedirs(logging_dir)
        pylab.savefig(os.path.join(logging_dir, "corr.pdf"))
        return coeff0[-1] - width + index


def fft_angles_and_intensities(image, border, logging_dir):
    """read image and create the angles and intensities
    in the frequency domain for the image.
    """
    F = np.fft.fft2(image)
    # clean up borders
    F[0:border,:] = 0; F[:, 0:border] = 0
    F[-border:] = 0; F[:, -border:] = 0
    # shift origin to the center of the freq-domain image
    F = np.fft.fftshift(F)
    # calculate angles
    sizey, sizex = F.shape
    x = np.arange(0, sizex, 1.) - sizex//2
    xx = np.tile(x, sizey).reshape(F.shape)
    y = np.arange(0, sizey, 1.) - sizey//2
    yy = np.repeat(y, sizex).reshape(F.shape)
    rho = (xx*xx + yy*yy)**.5
    angles = np.arctan2(yy, xx)
    # plot 
    # - angles
    pylab.figure(figsize=(5, 11))
    axes = plt.subplot(2,1,1)
    iaxes = pylab.imshow(angles)
    pylab.xlabel("angles")
    # - magnitude
    axes = plt.subplot(2,1,2)
    iaxes = pylab.imshow(np.log(np.abs(F)+1))
    pylab.colorbar()
    pylab.xlabel("magnitude")
    # - save
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)
    pylab.savefig(os.path.join(logging_dir, "freq-domain.pdf"))
    # clip along r axis
    R = min(image.shape) // 2
    bracket = (rho>0.1*R)*(rho<R)
    # return angles, np.abs(F)
    return angles[bracket], np.abs(F[bracket])
