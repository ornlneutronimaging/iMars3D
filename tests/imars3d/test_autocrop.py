#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
here = os.path.dirname(__file__)

import imars3d
from imars3d import io, autocrop

def test():
    dir = os.path.join(here, "..", "iMars3D_data_set", "turbine", "normalized")
    dir = os.path.abspath(dir)
    angles = np.arange(0., 10, 0.85)
    series = io.ImageFileSeries(os.path.join(dir, "normalized_%07.3f.*"), angles, decimal_mark_replacement='.')
    assert np.allclose(
        autocrop.calculateCropWindow(series),
        (50, 2047, 0, 2047)
    )
    return


def test2():
    dir = os.path.join(here, "..", "iMars3D_data_set", "autocrop", "darkboundaries")
    dir = os.path.abspath(dir)
    angles = np.arange(0., 10, 0.85)
    series = io.ImageFileSeries(os.path.join(dir, "20180704_Transmission_CT_%s_0080.*"), ['0010'])
    assert np.allclose(
        autocrop.calculateCropWindow(series),
        (627, 1442, 648, 1468)
    )
    return


def main():
    test()
    test2()
    return


if __name__ == '__main__': main()
