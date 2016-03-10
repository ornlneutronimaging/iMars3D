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


def test_recon_mpi_2cpu():
    layers = range(900, 905)
    recon_template = os.path.join("_tmp/test_mpi_2cpu", "recon_%05i.tiff")
    cmd = 'python -c "from imars3d.recon.mpi import recon_mpi; import numpy as np; recon_mpi(range(900,905), np.arange(0, 182, .85)*np.pi/180., %r, %r, stepsize=10)"' % (sinogram_template, recon_template)
    cmd = "mpirun -np 2 %s" % cmd
    if os.system(cmd):
        raise RuntimeError("%s failed" % cmd)
    return


def main():
    test_recon_mpi()
    test_recon_mpi_2cpu()
    return


if __name__ == '__main__': main()
