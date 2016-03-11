#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tell pytest to skip this test
import pytest
pytestmark = pytest.mark.skipif(True, reason="need large dataset")

import sys
import os, numpy as np, imars3d as i3

dir = os.path.dirname(__file__)
# datadir = os.path.join(dir, "..", "iMars3D_data_set", "turbine")
datadir = os.path.join(dir, "..", "iMars3D_large_dataset", "reconstruction", "turbine")
workdir = "_tmp/test_recon_chain/work"
outdir = "_tmp/test_recon_chain/out"
# dark field
pattern = os.path.join(datadir, "*DF*.fits")
dfs = i3.io.imageCollection(pattern, name="Dark Field")
# open beam
pattern = os.path.join(datadir, "*OB*.fits")
obs = i3.io.imageCollection(pattern, name="Open Beam")
# ct
angles = np.arange(0, 182, .85)
theta = angles * np.pi / 180.
ct_series = i3.io.ImageFileSeries(
    os.path.join(datadir, "*CT*_%.3f_*.fits"),
    identifiers = angles,
    name = "CT",
)

def test():
    normalized = i3.normalize(ct_series, dfs, obs, workdir=workdir)
    tilt_corrected = i3.correct_tilt(normalized, workdir=workdir)
    if_corrected = i3.correct_intensity_fluctuation(tilt_corrected, workdir=workdir)
    angles, sinograms = i3.build_sinograms(if_corrected, workdir=workdir)
    recon = i3.reconstruct(angles, sinograms, workdir=outdir)
    return

def main():
    test()
    return


if __name__ == '__main__': main()
