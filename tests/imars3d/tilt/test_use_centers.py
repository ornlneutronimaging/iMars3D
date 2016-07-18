#!/usr/bin/env python

import os, numpy as np
from imars3d import io
dir = os.path.dirname(__file__)
datadir = os.path.join(dir, "..", "..", 'iMars3D_data_set')

def main():
    img0 = os.path.join(datadir, 'injectorG/normalized_000.000.tiff')
    img180 = os.path.join(datadir, 'injectorG/normalized_180.000.tiff')
    img0 = io.ImageFile(img0)
    img180 = io.ImageFile(img180)
    from imars3d.tilt.use_centers import computeTilt
    computeTilt(img0, img180, workdir="_tmp.use_centers", sigma=3, maxshift=200)
    return

if __name__ == '__main__': main()
