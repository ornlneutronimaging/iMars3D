#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tell pytest to skip this test
import pytest
pytestmark = pytest.mark.skipif(True, reason="need large dataset")

import sys
import os, numpy as np, imars3d

dir = os.path.dirname(__file__)
# datadir = os.path.join(dir, "..", "iMars3D_data_set", "turbine")
datadir = os.path.join(dir, "..", "iMars3D_large_dataset", "reconstruction", "turbine")
workdir = "_tmp/test_components/work"
outdir = "_tmp/test_components/out"
# dark field
pattern = os.path.join(datadir, "*DF*.fits")
dfs = imars3d.io.imageCollection(pattern, name="Dark Field")
# open beam
pattern = os.path.join(datadir, "*OB*.fits")
obs = imars3d.io.imageCollection(pattern, name="Open Beam")
# ct
angles = np.arange(0, 182, .85)
theta = angles * np.pi / 180.
ct_series = imars3d.io.ImageFileSeries(
    os.path.join(datadir, "*CT*_%.3f_*.fits"),
    identifiers = angles,
    name = "CT",
)
# normalized ct
normalized_ct = imars3d.io.ImageFileSeries(
    os.path.join(outdir, "normalized_%.3f.tiff"), identifiers=angles, 
    decimal_mark_replacement=".",
    name="Normalized", mode="w"
)
# tilt corrected
tiltcorrected_series = imars3d.io.ImageFileSeries(
    os.path.join(outdir, "tiltcorrected_%.3f.tiff"),
    identifiers = angles,
    name = "Tilt corrected CT", mode = 'w',
)
# intensity fluctuation corrected
intfluct_corrected_series = imars3d.io.ImageFileSeries(
    os.path.join(outdir, "intfluctcorrected_%.3f.tiff"),
    identifiers = angles,
    name = "Intensity fluctuation corrected CT", mode = 'w',
)
# sinograms
sinograms = imars3d.io.ImageFileSeries(
    os.path.join(outdir, "sinogram_%i.tiff"),
    name = "Sinogram", mode = 'w',
)
# reconstructed
recon_series = imars3d.io.ImageFileSeries(
    os.path.join(outdir, "recon_%i.tiff"),
    name = "Sinogram", mode = 'w',
)


def test_normalization():
    # output
    normalization = imars3d.components.Normalization(workdir=workdir)
    normalization(ct_series, dfs, obs, normalized_ct)
    return


def test_tiltcalc():
    # ct
    angles = np.arange(0, 181, .85)
    ct_series = imars3d.io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = angles,
        name = "CT",
    )
    #
    tiltcalc = imars3d.components.TiltCalculation(workdir=workdir)
    tiltcalc(ct_series)
    return


def test_tiltcorr():
    tiltcorr = imars3d.components.TiltCorrection(tilt=-2.)
    tiltcorr(normalized_ct, tiltcorrected_series)
    return


def test_correct_intensity_fluctuation():
    ifcorr = imars3d.components.IntensityFluctuationCorrection()
    ifcorr(tiltcorrected_series, intfluct_corrected_series)
    return


def test_projection():
    proj = imars3d.components.Projection()
    proj(intfluct_corrected_series, sinograms)
    return


def test_recon():
    from imars3d.recon.mpi import recon
    recon_series.identifiers = sinograms.identifiers
    recon(sinograms, theta, recon_series, nodes=20)
    return


def main():
    # test_normalization()
    # test_tiltcalc()
    # test_tiltcorr()
    # test_correct_intensity_fluctuation()
    test_projection()
    test_recon()
    return


if __name__ == '__main__': main()
