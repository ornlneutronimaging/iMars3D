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

def filter_one(img, size):
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

# End of file
