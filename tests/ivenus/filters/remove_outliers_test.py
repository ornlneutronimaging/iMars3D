#!/usr/bin/env python

import numpy as np
from ivenus import filters

def test(interactive=False):
    # create an image with outliers
    from ivenus import sim
    img = sim.randomBG(100, 120, 100, 10);
    sim.addRandomOutliers(img, 100, 1000, 10)

    # filter
    threshold = 450
    filters.gamma_filtering.remove_outliers_bymedian(img, img>threshold)
    # validate
    assert(img[img>threshold].sum() == 0)
    if interactive:
        # display
        import pylab
        pylab.imshow(img)
        pylab.colorbar()
        pylab.show()
    return

if __name__ == '__main__':
    test(interactive=True)
