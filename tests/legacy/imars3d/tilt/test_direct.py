#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
from imars3d import io
from imars3d import tilt
from imars3d.tilt import direct
dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "iMars3D_data_set", "tilt", "16040")

def test_Calculator():
    # ct
    angles = np.arange(0, 180.5, 1.)
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "cropped*_%07.3f.tiff"),
        identifiers = angles,
        decimal_mark_replacement=".",
        name = "CT",
    )
    calculator = direct.DirectMinimization()
    t = tilt._compute(ct_series, "_tmp/test_direct/work", calculator=calculator)
    assert np.isclose(t, 0.4)
    return


def test_computeTilt():
    img0 = io.ImageFile(os.path.join(datadir, "cropped_000.000.tiff")).data
    img180 = io.ImageFile(os.path.join(datadir, "cropped_180.000.tiff")).data
    assert np.isclose( direct.computeTilt(img0, img180), 0.4 )
    return

def test_shift():
    img0 = io.ImageFile(os.path.join(datadir, "cropped_000.000.tiff")).data
    img180 = io.ImageFile(os.path.join(datadir, "cropped_180.000.tiff")).data
    flipped_180 = np.fliplr(img180)
    assert np.isclose( direct.findShift(img0, flipped_180), -78 )
    return

def main():
    test_shift()
    test_computeTilt()
    test_Calculator()
    return

if __name__ == '__main__': main()

# End of file
