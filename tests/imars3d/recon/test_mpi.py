#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import sys
import os, numpy as np, imars3d

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "iMars3D_data_set")
outdir = "_tmp/test_mpi"
# sinogram
layers = range(900, 905)
sinogram_template = os.path.join(datadir, "turbine", "sinogram_%i.tiff")
sinograms = imars3d.io.ImageFileSeries(
    sinogram_template,
    name = "Sinogram", identifiers = layers,
    )
angles = np.arange(0, 182, .85)
theta = angles * np.pi / 180.

def test_recon():
    from imars3d.recon.mpi import recon
    recon_template = os.path.join(outdir, "test_recon", "recon_%05i.tiff")
    recon_series = imars3d.io.ImageFileSeries(
        recon_template,
        mode = 'w', name = "Reconstructed", identifiers=layers,
        )
    recon(sinograms, theta, recon_series, nodes=5)
    return


def test_recon_mpi():
    from imars3d.recon.mpi import recon_mpi
    recon_template = os.path.join(outdir, "test_recon_mpi", "recon_%05i.tiff")
    recon_series = imars3d.io.ImageFileSeries(
        recon_template,
        mode = 'w', name = "Reconstructed", identifiers=layers,
        )
    recon_mpi(sinograms, theta, recon_series, stepsize=3)
    return


def test_recon_mpi_2cpu():
    workdir = dir
    pycode = """
import os, imars3d, numpy as np
datadir = os.path.join(%(workdir)r, "..", "..", "iMars3D_data_set")""" % locals()
    pycode += """
outdir = "_tmp/test_mpi/test_recon_mpi_2cpu"
# sinogram
layers = range(900, 905)
sinogram_template = os.path.join(datadir, "turbine", "sinogram_%i.tiff")
sinograms = imars3d.io.ImageFileSeries(
    sinogram_template,
    name = "Sinogram", identifiers = layers,
    )
# recon output
recon_template = os.path.join(outdir, "recon_%05i.tiff")
#
recon_series = imars3d.io.ImageFileSeries(
    recon_template,
    mode = 'w', name = "Reconstructed", identifiers=layers,
    )

# angles
angles = np.arange(0, 182, .85)
theta = angles * np.pi / 180.

# process
from imars3d.recon.mpi import recon_mpi
recon_mpi(sinograms, theta, recon_series, stepsize=1)
"""
    pypath = os.path.join(outdir, "test_recon_mpi_2cpu.py")
    open(pypath, 'wt').write(pycode)
    
    cmd = "mpirun -np 2 python %s" % pypath
    if os.system(cmd):
        raise RuntimeError("%s failed" % cmd)
    return


def main():
    test_recon_mpi()
    test_recon_mpi_2cpu()
    test_recon()
    return


if __name__ == '__main__':
    pytest.main([__file__])
