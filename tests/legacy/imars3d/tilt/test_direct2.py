#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
from imars3d import io
from imars3d import tilt
from imars3d.tilt import direct

dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine", "cleaned")


def test_computeTilt():
    img0 = io.ImageFile(os.path.join(datadir, "smoothed_000.000.tiff")).data
    img180 = io.ImageFile(os.path.join(datadir, "smoothed_180.200.tiff")).data
    t = direct.computeTilt(img0, img180)
    assert t > -2 and t < -1
    return


def main():
    test_computeTilt()
    return


if __name__ == "__main__":
    main()

# End of file
