#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
dir = os.path.dirname(__file__)
dir = os.path.join(dir, "..", "iMars3D_data_set", "turbine", "normalized")
dir = os.path.abspath(dir)

import imars3d

def test():
    from imars3d import io
    angles = np.arange(0., 10, 0.85)
    series = io.ImageFileSeries(os.path.join(dir, "normalized_%07.3f.*"), angles, decimal_mark_replacement='.')
    from imars3d import autocrop
    print autocrop.calculateCropWindow(series)
    return


if __name__ == '__main__': test()
