#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import sys
import os, numpy as np, imars3d

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "iMars3D_data_set")
outdir = "_tmp"
# sinogram
sinogram = imars3d.io.ImageFile(
    path = os.path.join(datadir, "turbine", "sinogram_900.tiff")
    )
angles = np.arange(0, 182, .85)
theta = angles * np.pi / 180.

def test_recon():
    from imars3d.recon.use_tomopy import recon
    out = os.path.join(outdir, "recon_900.tiff")
    recon(sinogram, theta, out)
    return

def test_recon_batch_singlenode():
    from imars3d.recon.use_tomopy import recon_batch_singlenode
    layers = range(901, 905)
    sinograms = imars3d.io.ImageFileSeries(
        os.path.join(datadir, "turbine", "sinogram_%i.tiff"),
        name = "Sinogram", identifiers = layers,
    )
    recon_series = imars3d.io.ImageFileSeries(
        os.path.join(outdir, "recon_%i.tiff"),
        mode = 'w', name = "Reconstructed", identifiers=layers,
        )
    recon_batch_singlenode(sinograms, theta, recon_series)
    return


def main():
    test_recon()
    test_recon_batch_singlenode()
    return


if __name__ == '__main__':
    pytest.main([__file__])
