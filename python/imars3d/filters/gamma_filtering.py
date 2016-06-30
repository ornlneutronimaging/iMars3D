# -*- python -*-
# -*- coding: utf-8 -*-


DESC = 'Gamma-filtering'
def filter_parallel(ct_series, output_img_series, **kwds):
    from .batch import filter_parallel
    return filter_parallel(
        ct_series, output_img_series, DESC, filter_one, **kwds)


def filter(ct_series, output_img_series, **kwds):
    from .batch import filter
    return filter(
        ct_series, output_img_series, DESC, filter_one, **kwds)


def filter_one(img, **kwds):
    """does gamma filtering on the given image
    - img: image npy array. must be of integer data type
    - kwds: additional kwd args to pass to remove_outliers_bymedian
    """
    max = np.iinfo(img.dtype).max
    threshold = max/2
    img = np.array(img, "float32")
    remove_outliers_bymedian(img, img>threshold, **kwds)
    return img


import numpy as np
def remove_outliers_bymedian(img, outlier_indexes, boxsize=5):
    """remove outliers from the given image by using median filtering
    just around the outliers. 
    - img: image npy array
    - outlier_indexes: indexes of outliers
    - boxsize: the size of the patch in which the median sampling is done
    """
    halfsize = boxsize//2
    img[outlier_indexes] = np.nan
    indexes = np.where(img!=img)
    for ind1, ind2 in zip(*indexes):
        img[ind1, ind2] = np.nanmedian(
            img[max(ind1-halfsize, 0):ind1+halfsize+1, max(ind2-halfsize, 0):ind2+halfsize+1])
        continue
    return img

# End of file
