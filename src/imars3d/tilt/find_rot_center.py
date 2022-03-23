
import os, numpy as np

def find(ct_series, workdir=None, max_npairs=20):
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    outpath = os.path.join(workdir, 'ROT_CENTER')
    if os.path.exists(outpath): # if already calculated, skip
        return float(open(outpath).read())
    img = lambda angle: ct_series.getImage(angle)
    from . import _find180DegImgPairs
    from .direct import findShift
    pairs = _find180DegImgPairs(ct_series.identifiers)
    centers = []
    for i, (a0, a180) in enumerate(pairs):
        if i>max_npairs: break # don't need too many pairs
        workdir1=os.path.join(workdir, "%s_vs_%s"%(a0, a180))
        shift = findShift(img(a0).data, np.fliplr(img(a180).data))
        center = -shift/2. + img(a0).data.shape[1]/2.
        # print shift, center, img(a0).data.shape[1]/2.
        centers.append(center)
        continue
    res = np.median(centers)
    open(outpath, 'wt').write(str(res))
    return res


def find_using_edges(ct_series, workdir=None):
    img = lambda angle: ct_series.getImage(angle)
    from . import _find180DegImgPairs
    from .use_centers import computeTilt
    pairs = _find180DegImgPairs(ct_series.identifiers)
    centers = []
    for i, (a0, a180) in enumerate(pairs):
        workdir1=os.path.join(workdir, "%s_vs_%s"%(a0, a180))
        slope, intercept = computeTilt(
            img(a0), img(a180), workdir=workdir1, 
            sigma=15, maxshift=200)
        center = intercept + slope * img(a0).data.shape[0]
        print(i, center)
        centers.append(center)
        continue
    return np.median(centers)
