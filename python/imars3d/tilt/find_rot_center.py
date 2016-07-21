
import os, numpy as np

def find(ct_series, workdir=None):
    img = lambda angle: ct_series.getImage(angle)
    from . import _find180DegImgPairs
    from .use_centers import computeTilt
    pairs = _find180DegImgPairs(ct_series.identifiers)
    centers = []
    for i, (a0, a180) in enumerate(pairs):
        workdir1=os.path.join(workdir, "%s_vs_%s"%(a0, a180))
        slope, intercept = computeTilt(
            img(a0), img(a180), workdir=workdir1, 
            sigma=10, maxshift=200)
        center = intercept + slope * img(a0).data.shape[0]
        print(i, center)
        centers.append(center)
        continue
    return np.mean(centers)
