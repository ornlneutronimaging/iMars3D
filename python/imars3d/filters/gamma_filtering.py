# -*- python -*-
# -*- coding: utf-8 -*-


def filter(ct_series, output_img_series, **kwds):
    """
    * ct_series: an image series for ct scan
    """
    prefix = "Gamma-filtering %s:" % ct_series.name or ""
    N = ct_series.nImages
    bar = progressbar.ProgressBar(
        widgets=[
            prefix,
            progressbar.Percentage(),
            progressbar.Bar(),
            ' [', progressbar.ETA(), '] ',
        ],
        max_value = N-1
    )
    for i, angle in enumerate(ct_series.identifiers):
        # skip over existing results
        if not output_img_series.exists(angle):
            data = ct_series.getData(angle)
            output_img_series.putImage(angle, filter_one(data, **kwds))
        bar.update(i)
        continue
    print
    return


def filter_one(img, **kwds):
    """does gamma filtering on the given image
    - img: image npy array. must be of integer data type
    - kwds: additional kwd args to pass to remove_outliers_bymedian
    """
    max = np.iinfo(img.dtype).max
    threshold = max/2
    img = np.array(img, np.float)
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
