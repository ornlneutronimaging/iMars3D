#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, numpy as np, imars3d

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "iMars3D_data_set")
# sinogram
sinogram = imars3d.io.ImageFile(
    path = os.path.join(datadir, "turbine", "sinogram_900.tiff")
    )

def test_recon():
    from imars3d.recon.use_tomopy import recon
    angles = np.arange(0, 182, .85)
    theta = angles * np.pi / 180.
    out = "recon_900.tiff"
    recon(sinogram, theta, out)
    return


def main():
    test_recon()
    return


if __name__ == '__main__': main()
