# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar
import os, sys, numpy as np


def recon_batch_singlenode(sinograms, theta, recon_series):
    """reconstruct from a bunch of sinograms.
This is intended to be run on just one node.

    theta: sample rotation angle in radian
    """
    import tomopy, imars3d.io
    proj = [img.data for img in sinograms]
    proj = np.array(proj)
    proj = np.swapaxes(proj, 0, 1)
    Y,X = proj[0].shape
    # reconstruct
    rec = tomopy.recon(
        proj,
        theta=theta, center=X/2.,
        algorithm='gridrec', emission=False,
        ncore = 1,
    )
    # output
    for i, img in enumerate(recon_series):
        img.data = rec[i]
        img.save()
        continue
    return


def recon(sinogram, theta, outpath):
    """Use tomopy to reconstruct from one sinogram
    
    theta: sample rotation angle in radian
    """
    import tomopy, imars3d.io
    proj = [sinogram.data]
    proj = np.array(proj)
    # tomopy.recon needs the shape to be
    # angles, Y, X
    proj = np.swapaxes(proj, 0, 1)
    Y,X = proj[0].shape
    # reconstruct
    rec = tomopy.recon(
        proj,
        theta=theta, center=X/2.,
        algorithm='gridrec', emission=False,
        ncore = 1,
    )
    rec = rec[0] # there is only one layer
    # output
    img = imars3d.io.ImageFile(path=outpath)
    img.data = rec
    img.save()
    return


# End of file
