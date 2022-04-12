#!/usr/bin/env python

import numpy as np, os
from imars3d import filters, io


def test(interactive=False):
    # test data
    dir = os.path.dirname(__file__)
    path = os.path.join(dir, "..", "..", "iMars3D_data_set", "20120618_TURBINECT_0180_46_750_0055.fits")
    img = io.ImageFile(path).getData()
    assert img.dtype == np.dtype("uint16")
    # force a pixel to be an outlier
    img[0, 0] = (1 << 16) - 1
    # filter
    orig_max = np.max(img)
    img = filters.gamma_filtering.filter_one(img)
    new_max = np.max(img)
    assert new_max < orig_max

    if interactive:
        # display
        import pylab

        pylab.imshow(img)
        pylab.colorbar()
        pylab.show()


if __name__ == "__main__":
    test(interactive=True)
