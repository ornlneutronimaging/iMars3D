# imars3d.tilt.use_centers

import os, numpy as np
from imars3d import io
from matplotlib import pyplot as plt

def computeTilt(img0path, img180path, workdir=None, **kwds):
    centers = np.array(
        [item for item 
         in iterCenters(img0path, img180path, workdir=workdir, **kwds)])
    rows, centers = centers.T
    cm = np.median(centers)
    csigma = np.std(centers)
    print("median=%s, stddev=%s" % (cm, csigma))
    w = (centers>cm-1.5*csigma) * (centers<cm+1.5*csigma)
    rows1 = rows[w]
    centers1 = centers[w]
    plt.figure()
    plt.plot(rows1, centers1)
    plt.savefig(os.path.join(workdir, "linefit.png"))
    plt.close()
    from scipy import stats
    slope, intercept, r, p, std_err = stats.linregress(rows, centers)
    print(slope, intercept)
    return


def iterCenters(img0path, img180path, workdir=None, sigma=3, maxshift=20):
    edge0 = getEdge(img0path, os.path.join(workdir, 'edge0.tiff'), sigma=sigma)
    edge180 = getEdge(img180path, os.path.join(workdir, 'edge180.tiff'), sigma=sigma)
    edge180 = edge180[:, ::-1]
    for i, (line0, line180) in enumerate(zip(edge0, edge180)):
        c = _computeCenterOfRot(line0, line180, maxshift=maxshift)
        yield i, c
        continue
    return

def getEdge(imgpath, edgepath, **kwds):
    img = io.ImageFile(imgpath).data
    from skimage import feature
    edge = feature.canny(img, **kwds)
    edge = np.array(edge, dtype="float32")
    edgeimg = io.ImageFile(path=edgepath)
    edgeimg.data = edge
    edgeimg.save()
    return edge

def _computeCenterOfRot(x1, x2, **kwds):
    shift = _computeShift(x1, x2, **kwds)
    return (shift + x1.size)/2.

def _computeShift(x1, x2, maxshift=20):
    """compute shift between two spectra
    when x1 is shifted by the result pixels, x1 is most similar to x2
    """
    diffs = []
    for dx in range(1-maxshift, maxshift):
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

