# -*- python -*-
# -*- coding: utf-8 -*-


DESC = "Ring artifact removal"


def filter_parallel(ct_series, output_img_series, **kwds):
    from .batch import filter_parallel

    return filter_parallel(ct_series, output_img_series, DESC, filter_one, **kwds)


def filter(ct_series, output_img_series, **kwds):
    from .batch import filter

    return filter(ct_series, output_img_series, DESC, filter_one, **kwds)


def filter_one(img, average_window_size=20, Nsubsets=10, correction_range=(0.9, 1.1)):
    """remove ring artifacts using the Ketcham method

    This only should be applied to sinograms

    - img: image npy array
    - average_window_size:
    - Nsubsets:
    """
    import numpy as np

    N = average_window_size
    corrections = []
    Nangles = img.shape[0]
    nangles_per_subset = int(np.ceil(Nangles * 1.0 / Nsubsets))
    c_min, c_max = correction_range
    for i in range(Nsubsets):
        start = i * nangles_per_subset
        end = min((i + 1) * nangles_per_subset, Nangles)
        x = img[start:end].sum(axis=0)
        y = np.convolve(x, np.ones(N, dtype=float) / N, "same")
        correction = y / x
        correction[:N] = 1
        correction[-N:] = 1
        correction[correction < c_min] = c_min
        correction[correction > c_max] = c_max
        corrections.append(correction)
        continue
    correction = np.median(corrections, axis=0)
    return img * correction[np.newaxis, :].astype("float32")


# End of file
