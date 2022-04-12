#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "raw")
CT_subdir = os.path.join("ct_scans", "Derek_injec")
workdir = "work"
outdir = "out"

import sys
import numpy as np, imars3d as i3, tomopy

from imars3d.CT import CT

ct = CT(datadir, CT_subdir=CT_subdir, CT_identifier="Derek_injec")
# dark field
dfs = i3.io.imageCollection(ct.DF_pattern, name="Dark Field")
# open beam
obs = i3.io.imageCollection(ct.OB_pattern, name="Open Beam")
# ct
angles = ct.angles
theta = angles * np.pi / 180.0
pattern = ct.CT_pattern
ct_series = i3.io.ImageFileSeries(pattern, identifiers=angles, name="CT")


def main():
    normalized = i3.normalize(ct_series, dfs, obs, workdir=os.path.join(workdir, "normalization"))
    tilt_corrected = i3.correct_tilt(normalized, workdir=os.path.join(workdir, "tilt-correction"))
    if_corrected = i3.correct_intensity_fluctuation(
        tilt_corrected, workdir=os.path.join(workdir, "intensity-fluctuation-correction")
    )
    angles, sinograms = i3.build_sinograms(if_corrected, workdir=os.path.join(workdir, "sinogram"))
    # take the middle part to calculate the center of rotation
    sino = [s.data for s in sinograms[900:1100]]
    sino = np.array(sino)
    proj = np.swapaxes(sino, 0, 1)
    rot_center = tomopy.find_center(proj, theta, init=1024, tol=0.5)
    rot_center = rot_center[0]
    # reconstruct
    recon = i3.reconstruct(angles, sinograms, workdir=outdir, center=rot_center)
    return


if __name__ == "__main__":
    main()
