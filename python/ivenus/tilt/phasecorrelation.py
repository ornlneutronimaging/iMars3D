#!/usr/bin/env python

import os, numpy as np
from scipy import ndimage
import pylab, matplotlib as mpl
from matplotlib import pyplot as plt
from .smooth import smooth
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
    
    def __init__(
        self, border=None, rotation=None, bins=None, logging_dir=None):
        self.border = border or self.__class__.border
        self.rotation = rotation or self.__class__.rotation
        self.bins = bins or self.__class__.bins
        self.logging_dir = logging_dir or self.__class__.logging_dir
        return
    
    def __call__(self, img0, img180):
        """
        implementation details:
        * the signal lines in the freq domain may overlap with
          x,y axes, where artifacts exist. so we rotate
          the input images by self.rotation
        """
        mpl.use("Agg")
        self._initProgress()
        # 0 degree data
        data0 = img0.getData()
        self._updateProgress()
        hist0 = self._computeIthetaHistogram(data0)
        # 180 degree data
        # print data0.shape
        data180 = img180.getData()
        self._updateProgress()
        # flip horizontally
        data180 = np.fliplr(data180)
        self._updateProgress()
        hist180 = self._computeIthetaHistogram(data180)
        # plot 
        pylab.figure(figsize=(5, 14))
        # - I(theta) histogram
        axes = plt.subplot(3,1,1)
        pylab.plot(hist0)
        pylab.plot(hist180)
        pylab.xlabel("I(theta)")
        # correlate
        r = self._correlate(hist0, hist180)
        # find peak position
        tilt = self._findPeakPosition(r)
        # plot
        # - save
        logging_dir = self.logging_dir
        if not os.path.exists(logging_dir):
            os.makedirs(logging_dir)
        pylab.savefig(os.path.join(logging_dir, "corr.pdf"))
        # make tilt center around 0
        if tilt > 180:
            tilt = tilt-360
        # tilt is the rotation angle divided by 2
        self._updateProgress()
        print
        return tilt/2
        
    
    def _computeIthetaHistogram(self, data0):
        data0 = ndimage.rotate(data0, self.rotation)
        self._updateProgress()
        sizeY, sizeX = data0.shape
        # only take the rectangle region where data exist
        data0 = data0[sizeY//4:sizeY*3//4, sizeX//4:sizeX*3//4]
        # create histogram
        angles0,F0 = fft_angles_and_intensities(
            data0, self.border, os.path.join(self.logging_dir, "0"), self._updateProgress)
        self._updateProgress()
        hist0, edges0 = np.histogram(angles0, weights=F0, bins=self.bins)
        self._updateProgress()
        return hist0

        
    def _correlate(self, hist0, hist180):
        # now that we have the histogram I(theta), we use 
        # phase correlation method to determine the shift
        hist0 = smooth(hist0)[:hist0.size]
        self._updateProgress()
        hist180 = smooth(hist180)[:hist180.size]
        self._updateProgress()
        iq0 = np.fft.fft(hist0)
        self._updateProgress()
        iq180 = np.fft.fft(hist180)
        self._updateProgress()
        # corr = iq0 * np.conjugate(iq180)
        corr = iq180 * np.conjugate(iq0)
        self._updateProgress()
        corr /= np.abs(corr)
        self._updateProgress()
        r = np.fft.ifft(corr)
        self._updateProgress()
        r = np.real(r)
        self._updateProgress()
        # plot
        # - phase correlation result
        axes = plt.subplot(3,1,2)
        iaxes = pylab.plot(r)
        pylab.xlabel("Correlation")
        self._updateProgress()
        return r
        
        
    def _findPeakPosition(self, r):
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
        self._updateProgress()
        # fitted peak
        peak_fit = poly2(x, *coeff0)
        # plot
        # - peak fitting
        axes = plt.subplot(3,1,3)
        pylab.plot(x, peak)
        pylab.plot(x, peak_fit)
        pylab.xlabel("Peak fitting")
        self._updateProgress()
        return coeff0[-1] - width + index


    def _initProgress(self):
        self._progress = 0
        import progressbar
        self._pbar = progressbar.ProgressBar(max_value = progressbar.UnknownLength)
        return
    def _updateProgress(self):
        self._progress += 1
        self._pbar.update(self._progress)
        return


def fft_angles_and_intensities(image, border, logging_dir, update_progress):
    """read image and create the angles and intensities
    in the frequency domain for the image.
    """
    F = np.fft.fft2(image)
    update_progress()
    # clean up borders
    F[0:border,:] = 0; F[:, 0:border] = 0
    F[-border:] = 0; F[:, -border:] = 0
    # shift origin to the center of the freq-domain image
    F = np.fft.fftshift(F)
    update_progress()
    # calculate angles
    sizey, sizex = F.shape
    x = np.arange(0, sizex, 1.) - sizex//2
    xx = np.tile(x, sizey).reshape(F.shape)
    update_progress()
    y = np.arange(0, sizey, 1.) - sizey//2
    yy = np.repeat(y, sizex).reshape(F.shape)
    update_progress()
    rho = (xx*xx + yy*yy)**.5
    angles = np.arctan2(yy, xx)
    update_progress()
    # plot 
    # - angles
    pylab.figure(figsize=(5, 11))
    axes = plt.subplot(2,1,1)
    iaxes = pylab.imshow(angles)
    pylab.xlabel("angles")
    update_progress()
    # - magnitude
    axes = plt.subplot(2,1,2)
    iaxes = pylab.imshow(np.log(np.abs(F)+1))
    pylab.colorbar()
    pylab.xlabel("magnitude")
    update_progress()
    # - save
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)
    pylab.savefig(os.path.join(logging_dir, "freq-domain.pdf"))
    update_progress()
    # clip along r axis
    R = min(image.shape) // 2
    bracket = (rho>0.1*R)*(rho<R)
    update_progress()
    # return angles, np.abs(F)
    return angles[bracket], np.abs(F[bracket])
