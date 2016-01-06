#!/usr/bin/env python

import numpy as np, pylab
from ivenus import filters

def test():
    # create an image with outliers
    from ivenus import sim
    img = sim.randomBG(100, 120, 100, 10);
    sim.addRandomOutliers(img, 100, 1000, 10)

    # filter
    threshold = 450
    filters.gamma_filtering.remove_outliers_bymedian(img, img>threshold)
    assert(img[img>threshold].sum() == 0)
    # return img for plotting when run interactively
    return img

if __name__ == '__main__':
    img = test()
    # display
    pylab.imshow(img)
    pylab.colorbar()
    pylab.show()
