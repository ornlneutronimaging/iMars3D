#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy
import tomopy.util.mproc as mproc
from skimage import feature
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
from functools import partial


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
        # use shared memory model and tqdm wrapper for multiprocessing
        with SharedMemoryManager() as smm:
            # create the shared memory
            shm = smm.SharedMemory(arrays.nbytes)
            # create a numpy array point to the shared memory
            shm_arrays = np.ndarray(
                arrays.shape,
                dtype=arrays.dtype,
                buffer=shm.buf,
            )
            # copy data
            np.copyto(shm_arrays, arrays)
            # map the multiprocessing calls
            rst = process_map(
                partial(intensity_fluctuation_correction_skimage, sigma=sigma),
                [img for img in shm_arrays],
                max_workers=ncore,
                desc="intensity_fluctuation_correction",
            )
        #
        return np.array(rst)
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
    NOTE:
    This method here is assuming the beam is decaying uniformly over time whereas
    the tomopy version is assuming different region decays slightly different, hence
    the linear interpolation between left and right air pixels.
    In most cases, a uniform decay is a good approximation as neutron beam tends
    to be very stable.

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
    # NOTE:
    #   1. Use canny edge detection to get a binary mask indicating which pixels is
    #   edge.
    #   2. If the background is somewhat noisy, the canny edge detection will always
    #   mark at least the second outmost ring of pixels as edge, therefore we will
    #   have at least one air pixels to work with, which is consistent with the
    #   default air=1 from tomopy.normalize_bg
    edge = feature.canny(image, sigma=sigma)
    # Find the middle col position, for a 512x512 image, this would be 255
    middle_col = (edge.shape[1] - 1) // 2
    # Use the middle col as starting guess for the left and right bound for each
    # row, we will move it to the left and right as we go through each row in the
    # image, i.e. finding the rough contour of the object.
    start_cols = np.ones(edge.shape[0], dtype=int) * middle_col
    stop_cols = np.ones(edge.shape[0], dtype=int) * middle_col
    for i, row in enumerate(edge):
        # here we are checking if there is any pixel marked to be an edge (True)
        # if there is at least one pixel, we will start moving the left and right
        # bound, otherwise we will keep them at the middle col, i.e. using the
        # whole row as the air pixels.
        isedge = row > 0
        if isedge.any():
            w = np.where(isedge)[0]
            # mark the first edge pixel to be the new left bound for current row,
            # and the last edge pixel to be the new right bound.
            start_cols[i], stop_cols[i] = w[0], w[-1]
    # get background
    _, n_cols = image.shape
    # Instead of blindly trusting the contour derived from canny edge detection,
    # we are using the middle pixel between the bound and the edge of the image
    # as the bound of the object.
    # For example, at row x from a image of 128x128, canny edge detection shows
    # the left bound is at 12 and right bound is at 120, we will move the two
    # bounds closer to the edge, i.e 6 as the new left bound, and 124 as the
    # right bound.
    start_cols = start_cols // 2
    stop_cols = (stop_cols + n_cols) // 2
    # compute bg
    # NOTE: We are gathering all pixels considered to be air pixels row by row.
    #       For example, in a image of 3x10 with left and right bounds at
    #       3, 8
    #       1, 7,
    #       2, 8
    #       the final collection of air pixels (1D array) will be
    #       [ img[0,0], img[0,1], img[0,2],
    #         img[1,0],
    #         img[2,0], img[2,1],
    #         img[0,7], img[0,8], img[0,9],
    #         img[1,6], img[1,7], img[1,8], img[1,9],
    #         img[0,7], img[0,8], img[0,9],
    #       ]
    #       the average value of the 1D array above will be used to normalize
    #       the corresponding image.
    left = np.array([])
    right = np.array([])
    for i, row in enumerate(image):
        left = np.concatenate((left, row[: start_cols[i]]))
        right = np.concatenate((right, row[stop_cols[i] :]))
    factor = np.concatenate((left, right)).mean()
    # apply the correction factor
    return image / factor
