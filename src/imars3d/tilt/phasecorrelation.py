#!/usr/bin/env python

import os, numpy as np
from scipy import ndimage
import pylab, matplotlib as mpl
from matplotlib import pyplot as plt
from .smooth import smooth
from scipy.optimize import curve_fit
from imars3d import configuration

pb_config = configuration["progress_bar"]


class PhaseCorrelation:

    # intensities in freq domain along x,y axes are always high
    # clearn them within the border size
    border = 0.01
    # see below doc in __call__
    rotation = 30.0  # 45.
    # this is for collecting I(theta) histogram.
    # better be integer multiplication of 360
    bins = 360
    logging_dir = "log.tilt-phasecorrelation"

    def __init__(self, border=None, rotation=None, bins=None, logging_dir=None):
        self.border = border or self.__class__.border
        assert self.border > 0
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
        hist0 = self._computeIthetaHistogram(data0, logging_subdir="0deg")
        # 180 degree data
        # print data0.shape
        data180 = img180.getData()
        self._updateProgress()
        # flip horizontally
        data180 = np.fliplr(data180)
        self._updateProgress()
        hist180 = self._computeIthetaHistogram(data180, logging_subdir="180deg")
        # plot
        pylab.figure(figsize=(5, 14))
        # - I(theta) histogram
        axes = plt.subplot(3, 1, 1)
        pylab.plot(hist0)
        pylab.plot(hist180)
        pylab.xlabel("I(theta)")
        # correlate
        r = self._correlate(hist0, hist180)
        # find peak position
        tilt, weight = self._findPeakPosition(r)
        # plot
        # - save
        logging_dir = self.logging_dir
        if not os.path.exists(logging_dir):
            os.makedirs(logging_dir)
        pylab.savefig(os.path.join(logging_dir, "corr.pdf"))
        # make tilt center around 0
        if tilt > 180:
            tilt = tilt - 360
        # tilt is the rotation angle divided by 2
        self._updateProgress()
        print()
        return tilt / 2, weight

    def _computeIthetaHistogram(self, data0, logging_subdir):
        logging_dir = os.path.join(self.logging_dir, logging_subdir)
        data0 = ndimage.rotate(data0, self.rotation)
        self._updateProgress()
        sizeY, sizeX = data0.shape
        # only take the rectangle region where data exist
        data0 = data0[sizeY // 4 : sizeY * 3 // 4, sizeX // 4 : sizeX * 3 // 4]
        # create histogram
        angles0, F0 = fft_angles_and_intensities(data0, self.border, logging_dir, self._updateProgress)
        self._updateProgress()
        hist0, edges0 = np.histogram(angles0, weights=F0, bins=self.bins)
        self._updateProgress()
        np.save(os.path.join(logging_dir, "I_theta_raw.npy"), hist0)
        # remove points around 0, 90, 180, 270
        for index in [0, 90, 180, 270]:
            remove_badpoints(hist0, index, 5)
            continue
        np.save(os.path.join(logging_dir, "I_theta.npy"), hist0)
        return hist0

    def _correlate(self, hist0, hist180):
        # now that we have the histogram I(theta), we use
        # phase correlation method to determine the shift
        hist0 = smooth(hist0)[: hist0.size]
        self._updateProgress()
        hist180 = smooth(hist180)[: hist180.size]
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
        axes = plt.subplot(3, 1, 2)
        iaxes = pylab.plot(r)
        pylab.xlabel("Correlation")
        self._updateProgress()
        np.save(os.path.join(self.logging_dir, "correlation.npy"), r)
        return r

    def _findPeakPosition(self, r):
        # the argmax of r should be what we want.
        # - only data within a few degrees are useful
        sigma = np.std(r[1:])  # need this later
        # take the spectrum around 0 degree
        WIDTH_TO_SEARCH = 10
        r1 = np.concatenate((r[-WIDTH_TO_SEARCH:], r[:WIDTH_TO_SEARCH]))
        r1[WIDTH_TO_SEARCH] = 0  # set value at 0 degree to zero
        index = np.argmax(r1)
        # check if the max value is larger than fluctuation
        if r1[index] < 3.5 * sigma:
            return 0, np.exp(-((r1[index] - sigma) ** 2) / 2 / sigma / sigma)
        # - fit the peak with a polynomial and get the high point
        width = 2
        if index - width <= 0:
            # XXX need more checking of this
            return 0, np.exp(-((r1[index] - sigma) ** 2) / 2 / sigma / sigma)
        weight = 1 - np.exp(-r1[index] ** 2 / 2 / sigma / sigma)
        peak = r1[index - width : index + width + 1]

        def poly2(x, *p):
            a0, a1, a2 = p
            return a0 - a1 * (x - a2) ** 2

        # initial guess for fit
        p0 = [r1[index], 1.0, width]
        # x axis
        x = np.arange(peak.size)
        # fit
        # import pdb; pdb.set_trace()
        coeff0, var_matrix = curve_fit(poly2, x, peak, p0=p0)
        self._updateProgress()
        # fitted peak
        peak_fit = poly2(x, *coeff0)
        # plot
        # - peak fitting
        axes = plt.subplot(3, 1, 3)
        pylab.plot(x, peak)
        pylab.plot(x, peak_fit)
        pylab.xlabel("Peak fitting")
        self._updateProgress()
        value = coeff0[-1] - width + index - WIDTH_TO_SEARCH
        return value, weight

    def _initProgress(self):
        self._progress = 0
        import progressbar

        self._pbar = progressbar.ProgressBar(max_value=progressbar.UnknownLength, **pb_config)
        return

    def _updateProgress(self):
        self._progress += 1
        self._pbar.update(self._progress)
        return


def fft_angles_and_intensities(image, border, logging_dir, update_progress):
    """read image and create the angles and intensities
    in the frequency domain for the image.
    """
    border = int(border * min(image.shape))
    # print("border=%s" % border)
    F = np.fft.fft2(image)
    update_progress()
    # clean up borders
    F[0:border, :] = np.nan
    F[:, 0:border] = np.nan
    F[-border:] = np.nan
    F[:, -border:] = np.nan
    # fill borders with zeros
    F[F != F] = 0
    # shift origin to the center of the freq-domain image
    F = np.fft.fftshift(F)
    update_progress()
    # calculate angles
    sizey, sizex = F.shape
    x = np.arange(0, sizex, 1.0) - sizex // 2
    xx = np.tile(x, sizey).reshape(F.shape)
    update_progress()
    y = np.arange(0, sizey, 1.0) - sizey // 2
    yy = np.repeat(y, sizex).reshape(F.shape)
    update_progress()
    rho = (xx * xx + yy * yy) ** 0.5
    angles = np.arctan2(yy, xx)
    update_progress()
    # plot
    # - angles
    pylab.figure(figsize=(5, 11))
    axes = plt.subplot(2, 1, 1)
    iaxes = pylab.imshow(angles)
    pylab.xlabel("angles")
    update_progress()
    # - magnitude
    axes = plt.subplot(2, 1, 2)
    iaxes = pylab.imshow(np.log(np.abs(F) + 1))
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
    bracket = (rho > 0.1 * R) * (rho < R)
    update_progress()
    # return angles, np.abs(F)
    return angles[bracket], np.abs(F[bracket])


def remove_badpoints(spectrum, index, width):
    assert width > 0
    good = np.median(
        np.concatenate((spectrum[index + width : index + 2 * width], spectrum[index - 2 * width : index - width]))
    )
    start = index - width
    end = index + width
    if start * end > 0:
        ranges = ((start, end),)
    elif start < 0 and end > 0:
        ranges = (start, -1), (0, end)
    else:
        raise ValueError("Don't know how to deal with region (%s, %s)" % (start, end))
    # assign good values to bad points
    for s, e in ranges:
        spectrum[s:e] = good
        continue
    return
