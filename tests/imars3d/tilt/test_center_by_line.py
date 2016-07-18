#!/usr/bin/env python

import os, numpy as np
from imars3d import io
from matplotlib import pyplot as plt
from skimage import feature
dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", 'iMars3D_data_set')

def getEdge(imgpath, edgepath, **kwds):
    img = io.ImageFile(imgpath).data
    edge = feature.canny(img, **kwds)
    edge = np.array(edge, dtype="float32")
    edgeimg = io.ImageFile(path=edgepath)
    edgeimg.data = edge
    edgeimg.save()
    return edge

def run(img0path, img180path, **kwds):
    edge0 = getEdge(img0path, 'edge0.tiff', **kwds)
    edge180 = getEdge(img180path, 'edge180.tiff', **kwds)
    edge180 = edge180[:, ::-1]
    for i, (line0, line180) in enumerate(zip(edge0, edge180)):
        c = _computeCenterOfRot(line0, line180)
        print i, c
        continue
    return

def _computeCenterOfRot(x1, x2):
    shift = _computeShift(x1, x2)
    return (shift + x1.size)/2.

def _computeShift(x1, x2):
    """compute shift between two spectra
    when x1 is shifted by the result pixels, x1 is most similar to x2
    """
    diffs = []
    for dx in range(-19, 20):
        if dx > 0:
            diff = x1[dx:] - x2[:-dx]
        elif dx < 0:
            diff = x1[:dx] - x2[-dx:]
        else:
            diff = x1-x2
        diff = np.sum(diff*diff)
        diffs.append((dx, diff))
    diffs = np.array(diffs)
    # np.save("diffs.npy", diffs)
    X,Y = diffs.T
    w = np.argmin(Y)
    return X[w]

def _correlate(hist0, hist180):
    # now that we have the histogram I(theta), we use 
    # phase correlation method to determine the shift
    iq0 = np.fft.fft(hist0)
    iq180 = np.fft.fft(hist180)
    # corr = iq0 * np.conjugate(iq180)
    corr = iq180 * np.conjugate(iq0)
    corr /= np.abs(corr)
    r = np.fft.ifft(corr)
    r = np.real(r)
    return r


def main():
    img0 = os.path.join(datadir, 'injectorG/normalized_000.000.tiff')
    img180 = os.path.join(datadir, 'injectorG/normalized_180.000.tiff')
    run(img0, img180, sigma=3)
    return

if __name__ == '__main__': main()
