# -*- python -*-
# -*- coding: utf-8 -*-

import numpy as np, sys

DESC = 'Smoothing'
def filter_parallel(ct_series, output_img_series, **kwds):
    from .batch import filter_parallel
    return filter_parallel(
        ct_series, output_img_series, DESC, filter_one, **kwds)


def filter(ct_series, output_img_series, **kwds):
    from .batch import filter
    return filter(
        ct_series, output_img_series, DESC, filter_one, **kwds)

def filter_one_median(img, size):
    """smoothing given image
    - img: image npy array
    - size: size of median filter
    """
    from scipy.ndimage import median_filter
    return median_filter(img, size)
    # convert to float32 if it is float
    typename = img.dtype.name
    if typename.startswith('float') and typename != 'float32':
        img = np.array(img, dtype="float32")
    import cv2
    return cv2.medianBlur(img, size)

def filter_one_bilateral(img, sigma_color=None, sigma_spatial=None):
    """smoothing using bilateral denoise
    - img: image npy array
    """
    from skimage.restoration import denoise_bilateral
    max = 1.*np.max(img)
    img = img.copy()
    img/=max
    img[img<0] = 0
    filtered = denoise_bilateral(img, sigma_color=sigma_color/max, sigma_spatial=sigma_spatial, multichannel=False)
    return (filtered * max).astype("float32")

def filter_one(img, algorithm='bilateral', **kwds):
    try:
        method = eval('filter_one_%s' % algorithm)
    except:
        raise RuntimeError("algorithm %s not implemented" % algorithm)
    return method(img, **kwds)


# End of file
