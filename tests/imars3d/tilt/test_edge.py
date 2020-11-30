#!/usr/bin/env python

import pytest
import os, numpy as np

def test():
    from skimage import feature
    from imars3d import io
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", 'iMars3D_data_set')
    imgpath = os.path.join(datadir, 'injectorG/normalized_000.000.tiff')
    img = io.ImageFile(imgpath).data
    edge = feature.canny(img, sigma=3)
    edge = np.array(edge, dtype="float32")
    edgeimg = io.ImageFile(path="edge_sigma3.tiff")
    edgeimg.data = edge
    edgeimg.save()
    return

if __name__ == '__main__':
    pytest.main([__file__])
