#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
from imars3d import io
from imars3d import tilt

def test_tilt():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine")
    # ct
    angles = np.arange(0, 181, .85)
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = angles,
        name = "CT",
    )
    from imars3d.tilt.phasecorrelation import PhaseCorrelation
    calculator = PhaseCorrelation()
    t = tilt._compute(ct_series, "_tmp/test_tilt/work", calculator=calculator)
    assert t>-2 and t<-1
    return
    

def test_tilt2():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine", "cleaned")
    # ct
    angles = np.arange(0, 181, .85)
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "smoothed*_%07.3f.tiff"),
        identifiers = angles,
        decimal_mark_replacement=".",
        name = "CT",
    )
    from imars3d.tilt.use_centers import Calculator
    calculator = Calculator(sigma=3, maxshift=200)
    t = tilt._compute(ct_series, "_tmp/test_tilt2/work", calculator=calculator)
    assert t>-1 and t<-.5
    return
    

def main():
    test_tilt()
    test_tilt2()
    return

if __name__ == '__main__': main()

# End of file
