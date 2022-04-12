#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, numpy as np, imars3d as i3, tomopy

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "IPTS-7878", "June19_2012")
datadir = "data"
workdir = os.path.join("work")
outdir = os.path.join("out")
# dark field
pattern = os.path.join(datadir, "DF", "*DF*.fits")
pattern = os.path.join(datadir, "*DF*.fits")
dfs = i3.io.imageCollection(pattern, name="Dark Field")
# open beam
pattern = os.path.join(datadir, "OB", "*OB*0180*.fits")
pattern = os.path.join(datadir, "*OB*0180*.fits")
obs = i3.io.imageCollection(pattern, name="Open Beam")
# ct
angles = np.arange(0, 182.0001, 0.35)
angles = np.arange(0, 181.90001, 0.85)
theta = angles * np.pi / 180.0
pattern = os.path.join(datadir, "TurbineCT", "*TURBNECT*_%.3f_*.fits")
pattern = os.path.join(datadir, "*TURBINECT*_%.3f_*.fits")
ct_series = i3.io.ImageFileSeries(
    pattern,
    identifiers=angles,
    name="CT",
)


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
