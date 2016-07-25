#!/usr/bin/env python

import os, numpy as np

def test():
    from imars3d import io
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", 'iMars3D_data_set')
    imgpath = os.path.join(datadir, 'injectorG/normalized_000.000.tiff')
    img = io.ImageFile(imgpath)
    
    from imars3d.components.ifc import getBg
    getBg(img, sigma=3)
    return

if __name__ == '__main__': test()
