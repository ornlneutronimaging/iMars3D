# -*- python -*-
# -*- coding: utf-8 -*-


DESC = "Cropping"


def filter_parallel(ct_series, output_img_series, **kwds):
    from .batch import filter_parallel

    return filter_parallel(ct_series, output_img_series, DESC, filter_one, **kwds)


def filter(ct_series, output_img_series, **kwds):
    from .batch import filter

    return filter(ct_series, output_img_series, DESC, filter_one, **kwds)


def filter_one(img, box=None):
    """cropping given image
    - img: image npy array
    - box: box of cropping
    """
    left, right, top, bottom = box
    img = img[top : bottom + 1, left : right + 1]
    return img


# End of file
