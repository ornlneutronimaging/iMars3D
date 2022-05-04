#!/usr/bin/env python3
import numpy as np
import scipy as sp


def crop(
    arrays: np.ndarray, slit_pos: tuple = (-1, -1, -1, -1), border_pix: int = 10, expand_ratio: float = 0.1
) -> np.ndarray:
    """
    Crop the image stack to the slit positions.

    o-------------------------------------------------------
    |                                                      |
    |     +++++++++++++++++top slit+++++++++++++++         |
    |     +                                      +         |
    |     +                                      +         |
    |   left slit           FOV               right slit   |
    |     +                                      +         |
    |     +                                      +         |
    |     +++++++++++++++++bottom slit+++++++++++++        |
    |                                                      |
    --------------------------------------------------------

    Parameters
    -----------
    @param arrays: np.ndarray
        The image stack to crop. Can also be a 2D image.
    @param slit_pos: tuple
        The slit positions. Default is (-1, -1, -1, -1), which will trigger
        the automatic detection of slit positions.
    @param border_pix: int
        the width of border region to estimate the slit positions for auto
        slit position detection.
    @param expand_ratio: float
        the ratio to expand the slit positions.

    Returns
    -------
    @return: np.ndarray
        The cropped image stack.
    """
    # check if slit positions are provided
    if -1 in slit_pos:
        slit_pos = detect_slit_positions(arrays, border_pix, expand_ratio)
    # crop
    left, right, top, bottom = slit_pos
    if arrays.ndim == 2:
        return arrays[top : bottom + 1, left : right + 1]
    elif arrays.ndim == 3:
        return arrays[:, top : bottom + 1, left : right + 1]
    else:
        raise ValueError("Only 2D and 3D arrays are supported.")


def detect_slit_positions(arrays: np.ndarray, border_pix: int = 10, expand_ratio: float = 0.1) -> tuple:
    """
    Detect the slit positions.

    @param arrays: np.ndarray
        The image stack to crop. Can also be a 2D image.
    @param border_pix: int
        the width of border region to estimate the background intensity
    @param expand_ratio: float
        the ratio to expand the slit positions.

    @return: tuple
        The slit positions in (left, right, top, bottom) order.
    """
    # generate representative image
    if arrays.ndim == 2:
        img = arrays
    elif arrays.ndim == 3:
        img = arrays.mean(axis=0)
    else:
        raise ValueError("Only 2D and 3D arrays are supported.")

    # denoise
    img = sp.ndimage.median_filter(img, 9)
    # rescale
    img /= img.max()
    # estimate background from four stripes near the border
    left = np.median(img[:, :border_pix])
    right = np.median(img[:, -border_pix:])
    top = np.median(img[:border_pix, :])
    bottom = np.median(img[-border_pix:, :])
    intensity_bg = np.median([left, right, top, bottom])

    # if background is dark
    if intensity_bg < 0.05:
        ys, xs = np.where(img > 0.1)
        dx = dy = 0.0  # no expanding needed
    else:
        # find the rectangle for real data
        ys, xs = np.where(img < intensity_bg * 0.95)
        #
        width = xs.max() - xs.min()
        height = ys.max() - ys.min()
        #
        dx = width * expand_ratio
        dy = height * expand_ratio

    # estimate the background intensity
    return (
        int(max(xs.min() - dx, 0)),
        int(min(xs.max() + dx, img.shape[1])),
        int(max(ys.min() - dy, 0)),
        int(min(ys.max() + dy, img.shape[0])),
    )
