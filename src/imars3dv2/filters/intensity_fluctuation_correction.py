#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy
import tomopy.util.mproc as mproc
from skimage import feature
import concurrent.futures as cf


def intensity_fluctuation_correction(
    arrays: np.ndarray,
    air_pixels: int = 5,
    sigma: int = 3,
    ncore: int = -1,
):
    """
    Correct for intensity fluctuation in the radiograph.

    Parameters
    ----------
    @param arrays:
        The image/radiograph stack to correct for beam intensity fluctuation.
    @param air_pixels:
        Number of pixels at each boundary to calculate the scaling factor. When a negative number
        is given, the auto air region detection will be used instead of tomopy.
    @param sigma:
        The standard deviation of the Gaussian filter, only valid when using the auto air region
        detection via canny edge detection from skimage.
    @param ncore:
        The number of cores to use for parallel processing, default is -1, which means using all available cores.

    Returns
    -------
    @return:
        The corrected image/radiograph stack.
    """
    # validation
    if arrays.ndim not in (2, 3):
        raise ValueError("The image/radiograph stack must be 2D or 3D.")
    # process
    if air_pixels < 0:
        # auto air region detection
        ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
        with cf.ProcessPoolExecutor(ncore) as e:
            jobs = [
                e.submit(
                    intensity_fluctuation_correction_skimage,
                    image,
                    sigma,
                )
                for image in arrays
            ]
        return np.array([job.result() for job in jobs])
    else:
        # use tomopy process
        ncore = None if ncore == -1 else int(ncore)
        return tomopy.normalize_bg(arrays, air=air_pixels, ncore=ncore)


def intensity_fluctuation_correction_skimage(
    image: np.ndarray,
    sigma: int = 3,
):
    """
    Correct for intensity fluctuation in the radiograph using skimage to auto
    detect the air region (adapted from iMars3dv1.filter.ifc).

    Parameters
    ----------
    @param image:
        The image/radiograph (2D) to correct for beam intensity fluctuation.
    @param sigma:
        The standard deviation of the Gaussian filter for the canny edge detection.

    Returns
    -------
    @return:
        The corrected image/radiograph (2D).
    """
    # get boundary
    edge = feature.canny(image, sigma=sigma)
    start_row = None
    middle_col = (edge.shape[1] - 1) // 2
    start_cols = np.ones(edge.shape[0], dtype=int) * middle_col
    stop_cols = np.ones(edge.shape[0], dtype=int) * middle_col
    for i, row in enumerate(edge):
        isedge = row > 0
        if isedge.any():
            w = np.where(isedge)[0]
            start_cols[i], stop_cols[i] = w[0], w[-1]
            # set the row that starts to have object to be measured
            if start_row is None:
                start_row = i
    # get background
    _, NCOLS = image.shape
    start_cols = start_cols // 2
    stop_cols = (stop_cols + NCOLS) // 2
    # compute bg
    left = None
    right = None
    for i, row in enumerate(image):
        _left = row[: start_cols[i]]
        _right = row[stop_cols[i] :]
        if left is None:
            left = _left
        else:
            left = np.concatenate((left, _left))
        if right is None:
            right = _right
        else:
            right = np.concatenate((right, _right))
    factor = np.concatenate((left, right)).mean()
    # apply the correction factor
    return image / factor
