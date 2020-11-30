#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
from imars3d import io
from imars3d.filters import normalizer

def test_average():
    dir = os.path.dirname(__file__)
    pattern = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine", "*DF*.fits")
    ic = io.imageCollection(pattern, name="Dark Field")
    a = normalizer.average(ic)
    return


def test_normalize():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine")
    # dark field
    pattern = os.path.join(datadir, "*DF*.fits")
    dfs = io.imageCollection(pattern, name="Dark Field")
    # open beam
    pattern = os.path.join(datadir, "*DF*.fits") # hack
    obs = io.imageCollection(pattern, name="Open Beam")
    # ct
    angles = np.arange(0, 52, 8.5)
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = angles,
        name = "CT",
    )
    # output
    normalized_ct = io.ImageFileSeries(
        "_tmp/test_normalizer/out/normalized_%.3f.npy", identifiers=angles, 
        decimal_mark_replacement=".", mode="w", name="Normalized"
        )
    normalizer.normalize(ct_series, dfs, obs, "_tmp/test_normalizer/work", normalized_ct)
    return
    

def test_normalize_noDF():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine")
    # dark field
    dfs = None
    # open beam
    pattern = os.path.join(datadir, "*DF*.fits") # hack
    obs = io.imageCollection(pattern, name="Open Beam")
    # ct
    angles = np.arange(0, 52, 8.5)
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = angles,
        name = "CT",
    )
    # output
    normalized_ct = io.ImageFileSeries(
        "_tmp/test_normalizer/out/normalized_%.3f.npy", identifiers=angles, 
        decimal_mark_replacement=".", mode="w", name="Normalized"
        )
    normalizer.normalize(ct_series, dfs, obs, "_tmp/test_normalizer/work", normalized_ct)
    return
    

def main():
    test_average()
    test_normalize()
    test_normalize_noDF()
    return

if __name__ == '__main__':
    pytest.main([__file__])

# End of file
