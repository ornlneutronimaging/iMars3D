# imars3d.tilt

import os, numpy as np
import logging

def compute(ct_series, workdir):
    logger = logging.getLogger("imars3d.tilt")
    tilt_out = os.path.join(workdir, "tilt.out")
    # cached value?
    if os.path.exists(tilt_out):
        return float(open(tilt_out).read())
    # computation
    from . import phasecorrelation
    img = lambda angle: ct_series.getImage(angle)
    # find opposite pairs
    pairs = _find180DegImgPairs(ct_series.identifiers)
    tilts = []
    for i, (a0, a180) in enumerate(pairs):
        logger.info("working on pair %s, %s" % (a0, a180))
        pc = phasecorrelation.PhaseCorrelation(
            logging_dir=os.path.join(workdir, "log.tilt.%s"%i))
        tilt = pc(img(a0), img(a180))
        tilts.append(tilt)
        logger.info("calculated tilt: %s" % tilt)
        continue
    tilt = np.average(tilts)
    # save to cache
    open(tilt_out, 'wt').write(str(tilt))
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
    from scipy import ndimage
    import numpy as np
    
    data = img.getData()
    data = ndimage.rotate(data, -tilt)
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
