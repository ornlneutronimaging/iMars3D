#!/usr/bin/env python

import os, numpy as np
from ivenus import io

def test():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "../../iVenus_data_set/turbine")
    ct_series = io.ImageFileSeries(
        os.path.join(datadir, "*CT*_%.3f_*.fits"),
        identifiers = np.arange(0, 52, 8.5),
    )

    assert (os.path.basename(ct_series.getFilename(0)) == "20120618_TURBINECT_0180_0_000_0000.fits")
    img = ct_series.getImage(0)
    data = img.getData()
    data = ct_series.getData(0)
    return


def main():
    test()
    return


if __name__ == "__main__": main()
