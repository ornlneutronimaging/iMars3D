#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, numpy as np, ivenus

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "iVenus_data_set", "turbine")
workdir = "_tmp/test_components/work"
outdir = "_tmp/test_components/out"
# dark field
pattern = os.path.join(datadir, "*DF*.fits")
dfs = ivenus.io.imageCollection(pattern, name="Dark Field")
# open beam
pattern = os.path.join(datadir, "*DF*.fits")
obs = ivenus.io.imageCollection(pattern, name="Open Beam")
# ct
angles = np.arange(0, 52, 8.5)
ct_series = ivenus.io.ImageFileSeries(
    os.path.join(datadir, "*CT*_%.3f_*.fits"),
    identifiers = angles,
    name = "CT",
)
# normalized ct
normalized_ct = ivenus.io.ImageFileSeries(
    os.path.join(outdir, "normalized_%.3f.npy"), identifiers=angles, 
    decimal_mark_replacement=".",
    name="Normalized", mode="w"
)
# tilt corrected
tiltcorrected_series = ivenus.io.ImageFileSeries(
    os.path.join(outdir, "tiltcorrected_%.3f.npy"),
    identifiers = angles,
    name = "Tilt corrected CT", mode = 'w',
)
# sinograms
sinograms = ivenus.io.ImageFileSeries(
    os.path.join(outdir, "sinogram_%i.npy"),
    name = "Sinogram", mode = 'w',
)


def test_normalization():
    # output
    normalization = ivenus.components.Normalization(workdir=workdir)
    normalization(ct_series, dfs, obs, normalized_ct)
    return


def test_tiltcalc():
    # ct
    angles = np.arange(0, 181, .85)
    ct_series = ivenus.io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = angles,
        name = "CT",
    )
    #
    tiltcalc = ivenus.components.TiltCalculation(workdir=workdir)
    tiltcalc(ct_series)
    return


def test_tiltcorr():
    tiltcorr = ivenus.components.TiltCorrection(tilt=-2.)
    tiltcorr(ct_series, tiltcorrected_series)
    return


def test_projection():
    proj = ivenus.components.Projection()
    proj(ct_series, sinograms)
    return


def main():
    # test_normalization()
    # test_tiltcalc()
    # test_tiltcorr()
    test_projection()
    return


if __name__ == '__main__': main()
