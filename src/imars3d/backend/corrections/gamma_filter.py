#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy


def gamma_filter(
    arrays: np.ndarray,
    threshold: int = -1,
    median_kernel: int = 5,
    axis: int = 0,
    ncore: int = -1,
    selective_median_filter: bool = True,
    diff_tomopy: float = -1.0,
) -> np.ndarray:
    """
    Replace near saturated pixels (due to gamma radiation) with median values.
    The median filtering is carried out by tomopy.remove_outlier.
    If selective median filtering is enabled (default), only the pixels greater than the specified threshold are replaced.

    Parameters
    ----------
    arrays:
        3D array of images, the first dimension is the rotation angle omega
    threshold:
        threshold for saturation, default is -1, which means using the internally defined threshold (see source code)
    median_kernel:
        size of the median filter kernel, default is 5
    axis:
        axis along which to chunk the array for parallel median filtering, default is 0.
    ncore:
        number of cores to use for parallel median filtering, default is -1, which means using all available cores.
    selective_median_filter:
        whether to use selective median filtering, default is True.
    diff_tomopy:
        threshold passed to tomopy for median filter based outlier detection. Negative values will use the internal default value (see source code).

    Returns
    -------
        corrected 3D array of images, the first dimension is the rotation angle omega
    """
    # parse input
    saturation_intensity = np.iinfo(arrays.dtype).max
    threshold = saturation_intensity - 5 if threshold == -1 else threshold
    #
    ncore = None if ncore == -1 else ncore
    # NOTE: use 20% of the total dynamic range as the outlier detection criterion
    diff_tomopy = 0.2 * saturation_intensity if diff_tomopy < 0.0 else diff_tomopy
    # median filtering
    arrays_filtered = tomopy.remove_outlier(arrays, dif=diff_tomopy, size=median_kernel, axis=axis, ncore=ncore)
    # selective replacement
    if selective_median_filter:
        arrays_filtered = np.where(arrays > threshold, arrays_filtered, arrays)
    # return
    return arrays_filtered
