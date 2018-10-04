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
        (0, 2047, 33, 2047)
    )
    return


def test2():
    dir = os.path.join(here, "..", "iMars3D_data_set", "autocrop", "darkboundaries")
    dir = os.path.abspath(dir)
    angles = np.arange(0., 10, 0.85)
    series = io.ImageFileSeries(os.path.join(dir, "20180704_Transmission_CT_%s_0080.*"), ['0010'])
    # print autocrop.calculateCropWindow(series, normalize=True)
    assert np.allclose(
        autocrop.calculateCropWindow(series, normalize=True),
        (627, 1442, 648, 1468)
    )
    return


def test2a():
    dir = os.path.join(here, "..", "iMars3D_data_set", "autocrop", "darkboundaries")
    dir = os.path.abspath(dir)
    series = io.ImageFileSeries(
        os.path.join(dir, "20180918_A49_4_CT_afterStableCycling_normalized_%7.3f.tiff"),
        [300.300],
        decimal_mark_replacement='.',
    )
    # print autocrop.calculateCropWindow(series)
    assert np.allclose(
        autocrop.calculateCropWindow(series),
        (767, 1309, 566, 1163),
    )
    return


def test3():
    dir = os.path.join(here, "..", "iMars3D_data_set", "autocrop", "dark-bottom")
    dir = os.path.abspath(dir)
    series = io.ImageFileSeries(os.path.join(dir, "sm-estimate-ave%s.tiff"), [''])
    # print autocrop.calculateCropWindow(series)
    assert np.allclose(
        autocrop.calculateCropWindow(series),
        (0, 2047, 1166, 2047)
    )
    return


def test4():
    dir = os.path.join(here, "..", "iMars3D_data_set", "autocrop")
    dir = os.path.abspath(dir)
    series = io.ImageFileSeries(os.path.join(dir, "bright_stripe_bottom_left%s.tiff"), [''])
    assert np.allclose(
        autocrop.calculateCropWindow(series),
        (689, 1318, 28, 2047)
    )
    return


def main():
    test()
    test2()
    test2a()
    test3()
    test4()
    return


if __name__ == '__main__': main()
