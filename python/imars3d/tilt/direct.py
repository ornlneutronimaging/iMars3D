# imars3d.tilt.direct

"""
directly compute tilt in real space 
* no fft to compute polar distribution like in phasecorrelation
* no edge detection like in use_centers

Just simply 
* find the center of rotation
* find rotation angle by doing a minimization
"""

import os, numpy as np
from imars3d import io
from matplotlib import pyplot as plt
from skimage.transform import rotate


class DirectMinimization:

    def __init__(self, logging_dir=None, **opts):
        self.logging_dir = logging_dir
        self.opts = opts
        return
    
    def __call__(self, img0, img180):
        return computeTilt(img0.data, img180.data, workdir=self.logging_dir), 1.0


def computeTilt(img0, img180, workdir=None, **kwds):
    flipped_img180 = np.fliplr(img180)
    shift = findShift(img0, flipped_img180)
    tilts = np.arange(-2., 2.1, 0.2)
    tilt = _argmin_tilt(tilts, img0, flipped_img180, shift, workdir=workdir)
    tilts = np.arange(tilt-0.2, tilt+0.21, 0.02)
    tilt = _argmin_tilt(tilts, img0, flipped_img180, shift, workdir=workdir)
    return tilt


def _argmin_tilt(tilts, img0, flipped_img180, shift, workdir=None):
    diffs = []
    if workdir:
        logfile = open(os.path.join(workdir, 'log._argmin_tilt'), 'wt')
    for tilt in tilts:
        diff = shift_tilt_diff(shift, tilt, img0, flipped_img180)
        diff = np.sum( diff**2 ) / diff.size
        if workdir:
            logfile.write("* tilt=%s, diff=%s\n" % (tilt, diff))
        diffs.append(diff)
        continue
    return tilts[np.argmin(diffs)]


def shift_tilt_diff(shift, tilt, img1, img2):
    nrows, ncols = img1.shape
    borderY, borderX = nrows//20, ncols//20
    a = rotate(img1/np.max(img1), -tilt)[borderY:-borderY, borderX:-borderX]
    b = rotate(img2/np.max(img2), tilt)[borderY:-borderY, borderX:-borderX]
    return shift_diff(shift, a, b)

        
def shift_diff(x, img1, img2):
    # shift positive means img2 was shifted to the left,
    # or img1 was shifted to the right.
    x = int(x)
    if x>0:
        left = img1[:, :-x]
        right = img2[:, x:]
    elif x<0:
        left = img1[:, -x:]
        right = img2[:, :x]
    else:
        left = img1
        right = img2
    return left-right


def shift_diff2(x, img1, img2):
    d = shift_diff(x, img1, img2)
    return (d**2).sum()/d.size

MAX_SHIFT = 400
def findShift(img0, flipped_img180):
    """find the shift in number of pixels
    
    note: the relation between rot center and shift is
      rot_center = -shift/2 if 0 is center of image
    """
    # print("* Calculating shift...")
    ncols = img0.shape[1]
    def diff(x):
        return shift_diff2(x, img0, flipped_img180)
    start = max(-ncols//2, -MAX_SHIFT)
    end = min(MAX_SHIFT, ncols//2)
    xs = range(start, end)
    diffs = [diff(x) for x in xs]
    index = np.argmin(diffs)
    guess = xs[index]
    return guess
    assert index >=5 and index < len(xs)-6
    # around guess
    x = xs[index-3: index+4]
    y = diffs[index-3: index+4]
    plt.plot(x,y)
    plt.savefig("tilt-direct-around-guess.png")
    # fit to parabolic
    a = np.polyfit(x,y,2)
    c = -a[1]/2/a[0]
    return c


def findShift_byfft(img0, flipped_img180):
    "compute shift from img0 to the flipped img180"
    import numpy.fft as npfft, numpy as np
    A = npfft.fft2(1-img0)
    B = npfft.fft2(1-flipped_img180)
    C = A * np.conjugate(B)
    C /= np.abs(C)
    D = npfft.ifft2(C)
    plt.imshow(np.real(D))
    plt.savefig("D.png")
    pos = np.argmax(D)
    nrows, ncols = D.shape
    col = pos % ncols
    row = pos // ncols
    # should be around zero
    if row > nrows//10:
        row -= nrows
    if col > ncols//10:
        col -= ncols
    if abs(row) > nrows//10 or abs(col) > ncols//10:
        msg = "computed displacement unexpectedly too large: %s, %s"% (
            col, row)
        raise RuntimeError(msg)
    return col, row
