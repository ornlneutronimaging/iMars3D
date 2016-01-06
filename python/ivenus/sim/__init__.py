# simulate images

import numpy as np

def randomBG(xsize, ysize, center, fluctuation):
    """random image of given size with values fluctating around the given center value"""
    return np.random.randn(xsize, ysize) * fluctuation + center


def addRandomOutliers(img, N, center, fluctuation):
    """add N random outliers into the image
    with values fluctating around the given center value
    """
    indexes = np.random.random_integers(0, img.size, N)
    saved = img.shape
    img.shape = -1,
    img[indexes] = np.random.randn(N) * fluctuation + center
    img.shape = saved
    return img

