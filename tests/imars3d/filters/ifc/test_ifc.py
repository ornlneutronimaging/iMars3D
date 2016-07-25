#!/usr/bin/env python

import os, numpy as np
from imars3d.filters import ifc

from imars3d import io
dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", "..", 'iMars3D_data_set')
imgpath = os.path.join(datadir, 'injectorG/normalized_000.000.tiff')
img = io.ImageFile(imgpath)


def test_getBoundary():
    ifc.getBoundary(img.data, sigma=3, debug=True)
    return

def test_getBG():
    print(ifc.getBG(img.data, sigma=3, debug=True))
    return

def test_filter_one():
    newimg = io.ImageFile('ifced.tiff')
    newimg.data = ifc.filter_one(img.data, sigma=3)
    newimg.save()
    return

def main():
    test_getBoundary()
    test_getBG()
    test_filter_one()
    return

if __name__ == '__main__': main()
