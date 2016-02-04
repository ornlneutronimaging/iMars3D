#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, numpy as np
from ivenus import io
from ivenus import tilt

def test_tilt():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", "iVenus_data_set", "turbine")
    # ct
    angles = np.arange(0, 181, .85)
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = angles,
        name = "CT",
    )
    print(tilt.compute(ct_series, "_tmp/test_tilt/work"))
    return
    

def main():
    test_tilt()
    return

if __name__ == '__main__': main()

# End of file
