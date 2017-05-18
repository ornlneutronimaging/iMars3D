# imars3d.tilt

import os, numpy as np, warnings
import logging
from . import use_centers, phasecorrelation, direct

def compute(ct_series, workdir, max_npairs=10):
    from . import use_centers
    calculators = [
        direct.DirectMinimization(),
        use_centers.UseCenters(sigma=15, maxshift=200),
        phasecorrelation.PhaseCorrelation(),
        ]
    tilt = None
    for calculator in calculators:
        kind = calculator.__class__.__name__
        # print kind
        try:
            tilt = _compute(
                ct_series, os.path.join(workdir, kind),
                max_npairs=10,
                calculator=calculator)
            # print tilt
            break
        except:
            warnings.warn("Failed to use %s to determine tilt" % kind)
        continue
    if tilt is None:
        raise RuntimeError("Failed to compute tilt")
    return tilt

def _compute(ct_series, workdir, max_npairs=10, calculator=None):
    logger = logging.getLogger("imars3d.tilt")
    tilt_out = os.path.join(workdir, "tilt.out")
    # cached value?
    if os.path.exists(tilt_out):
        return float(open(tilt_out).read())
    # computation
    if not calculator:
        # from . import phasecorrelation
        # calculator = phasecorrelation.PhaseCorrelation()
        calculator = use_centers.Calculator(sigma=10, maxshift=200)
    img = lambda angle: ct_series.getImage(angle)
    # find opposite pairs
    pairs = _find180DegImgPairs(ct_series.identifiers)
    tilts = []
    for i, (a0, a180) in enumerate(pairs):
        if max_npairs is not None and i>max_npairs:
            break # don't need too many pairs
        logger.info("working on pair %s, %s" % (a0, a180))
        logging_dir=os.path.join(workdir, "log.tilt.%s_vs_%s"%(a0, a180))
        if not os.path.exists(logging_dir):
            os.makedirs(logging_dir)
            calculator.logging_dir=logging_dir
            tilt, weight = calculator(img(a0), img(a180))
            open(os.path.join(logging_dir, 'tilt.out'), 'wt')\
                .write("%s\t%s\n" % (tilt, weight))
        else:
            s = open(os.path.join(logging_dir, 'tilt.out'), 'rt').read()
            s = s.strip()
            tilt, weight = map(float, s.split())            
        tilts.append((tilt, weight))
        logger.info("calculated tilt: %s. weight: %s" % (tilt, weight))
        continue
    tilts = np.array(tilts)
    tilts, weights = tilts.T
    tilt = (tilts * weights).sum() / weights.sum()
    hist,edges = np.histogram(tilts, bins=np.arange(-5.1, 5.2, 0.2), weights=weights)
    maxind = np.argmax(hist)
    bracket = edges[maxind], edges[maxind+1]
    condition = (tilts<bracket[1]+0.1) * (tilts>bracket[0]-0.1)
    tilts2 = tilts[ condition ]
    weights2 = weights[condition]
    tilt2 = (tilts2 * weights2).sum() / weights2.sum()
    logger.info("tilt2 was calculated from: %s samples out of total of %s" % (
        weights2.sum(), weights.sum()))
    # save to cache
    open(tilt_out, 'wt').write(str(tilt))
    tilt_out2 = os.path.join(workdir, "tilt.out2")
    open(tilt_out2, 'wt').write(str(tilt2))
    return tilt


def check(tilt, img0, img180):
    """check tilt using a pair of images
    """
    from imars3d import io
    apply(tilt, img0, io.ImageFile("tilted-0.npy"))
    apply(tilt, img180, io.ImageFile("tilted-180.npy"))
    return


def apply(tilt, img, outimg, save=True):
    """apply tilt to the given image
    """
    # from scipy import ndimage
    from skimage.transform import rotate
    import numpy as np
    
    data = img.getData()
    # data = ndimage.rotate(data, -tilt)
    data = rotate(data, -tilt)
    outimg.data = data
    if save:
        outimg.save()
    return


# 
def _find_nearest(value, array):
    idx = (np.abs(array-value)).argmin()
    return array[idx]

def _find180DegImgPairs(angles, tolerance=0.3):
    step = angles[1] - angles[0]
    for angle in angles:
        opposite = _find_nearest(angle+180, angles)
        # if beyond the end of the array, we are done
        if opposite - angles[-1] > step/2: break
        # check 
        if abs(opposite - angle-180) < tolerance:
            yield angle, opposite
        continue
    return
