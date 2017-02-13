# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar
import os, sys, numpy as np


def recon_batch_singlenode(
        sinograms, theta, recon_series, center=None,
        algorithm='gridrec', emission=False, **kwds):
    """reconstruct from a bunch of sinograms.
This is intended to be run on just one node.

    theta: sample rotation angle in radian
    """
    import tomopy, imars3d.io
    proj = [img.data for img in sinograms]
    proj = np.array(proj)
    proj = np.swapaxes(proj, 0, 1)
    Y,X = proj[0].shape
    if center is None:
        center = X/2.
    # reconstruct
    algorithm = algorithm or 'gridrec'
    # algorithm='fbp',
    # lgorithm='pml_hybrid',
    rec = tomopy.recon(
        proj,
        theta=theta, center=center,
        algorithm=algorithm, emission=emission,
        ncore = 1, **kwds
    )
    # output
    for i, img in enumerate(recon_series):
        img.data = rec[i]
        img.save()
        continue
    return


def recon(sinogram, theta, outpath, center=None,
          algorithm='gridrec', emission=False, ncore=1, **kwds):
    """Use tomopy to reconstruct from one sinogram
    
    theta: sample rotation angles in radian
    """
    import tomopy, imars3d.io
    proj = [sinogram.data]
    proj = np.array(proj)
    # tomopy.recon needs the shape to be
    # angles, Y, X
    proj = np.swapaxes(proj, 0, 1)
    Y,X = proj[0].shape
    if center is None:
        center = X/2.
    # reconstruct
    rec = tomopy.recon(
        proj,
        theta=theta, center=center,
        algorithm=algorithm,
        emission=emission,
        ncore = ncore,
        **kwds
    )
    rec = rec[0] # there is only one layer
    # output
    img = imars3d.io.ImageFile(path=outpath)
    img.data = rec
    img.save()
    return


# End of file
