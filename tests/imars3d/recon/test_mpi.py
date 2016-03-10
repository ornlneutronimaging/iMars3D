#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, numpy as np, imars3d

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "iMars3D_data_set")
outdir = "_tmp/test_mpi"
# sinogram
sinogram_template = os.path.join(datadir, "turbine", "sinogram_%i.tiff")
recon_template = os.path.join(outdir, "recon_%05i.tiff")
angles = np.arange(0, 182, .85)
theta = angles * np.pi / 180.

def test_recon_mpi():
    from imars3d.recon.mpi import recon_mpi
    layers = range(900, 905)
    recon_mpi(layers, theta, sinogram_template, recon_template, stepsize=10)
    return


def main():
    test_recon_mpi()
    return


if __name__ == '__main__': main()
