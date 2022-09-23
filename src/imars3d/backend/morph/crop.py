#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from scipy.ndimage import median_filter


def crop(
    arrays: np.ndarray,
    crop_limit: tuple = (-1, -1, -1, -1),
    border_pix: int = 10,
    expand_ratio: float = 0.1,
    rel_intensity_threshold_air_or_slit: float = 0.05,
    rel_intensity_threshold_fov: float = 0.1,
    rel_intensity_threshold_sample: float = 0.95,
) -> np.ndarray:
    """
    Crop the image stack to provided limits or auto detected bound box.

    Parameters
    -----------
    arrays:
        The image stack to crop. Can also be a 2D image.
    crop_limit:
        The four limits for cropping. Default is (-1, -1, -1, -1), which will trigger
        the automatic bounds detection.
    border_pix:
        the width of border region to estimate the background intensity, which helps
        to determine which case we are in.
    expand_ratio:
        the ratio to expand the cropped region.
    rel_intensity_threshold_air_or_slit:
        passing through keyword arguments to detect_bounds.
    rel_intensity_threshold_fov:
        passing through keyword arguments to detect_bounds.
    rel_intensity_threshold_sample:
        passing through keyword arguments to detect_bounds.

    Returns
    -------
        The cropped image stack.
    """
    # Notes
    # -----
    #     Case 1: slits in, i.e I_inner >> I_outer
    # o*******************************************************
    # |        low                                           |
    # |     +++++++++++++++++top slit+++++++++++++++         |
    # |     +                                      +         |
    # |     +                                      +         |
    # |   left slit           FOV(high)         right slit   |
    # |     +                                      +         |
    # |     +                                      +         |
    # |     +++++++++++++++++bottom slit+++++++++++++        |
    # |                                                      |
    # ********************************************************
    #
    # Case 2: slits out, i.e I_inner < I_outer
    # o*******************************************************
    # |                                                      |
    # |            *****************                         |
    # |             *    object   *           air            |
    # |              *   (low)   *           (high)          |
    # |               ***********                            |
    # ********************************************************
    #
    # NOTE: fails early if the array dimension is incorrect
    if arrays.ndim not in (2, 3):
        raise ValueError("Only 2D and 3D arrays are supported.")

    # check if crop limits (bounding box) are provided
    if -1 in crop_limit:
        crop_limit = detect_bounds(
            arrays,
            border_pix,
            expand_ratio,
            rel_intensity_threshold_air_or_slit,
            rel_intensity_threshold_fov,
            rel_intensity_threshold_sample,
        )
    # crop
    left, right, top, bottom = crop_limit
    if arrays.ndim == 2:
        return arrays[top:bottom, left:right]
    elif arrays.ndim == 3:
        return arrays[:, top:bottom, left:right]


def detect_bounds(
    arrays: np.ndarray,
    border_pix: int = 10,
    expand_ratio: float = 0.1,
    rel_intensity_threshold_air_or_slit: float = 0.05,
    rel_intensity_threshold_fov: float = 0.1,
    rel_intensity_threshold_sample: float = 0.95,
) -> tuple:
    """
    Auto detect bounds based on intensity thresholding.

    Parameters
    -----------
    arrays:
        The image stack to crop. Can also be a 2D image.
    border_pix:
        the width of border region to estimate the background intensity
    expand_ratio:
        the ratio to expand the cropped region.
    rel_intensity_threshold_air_or_slit:
        the relative intensity threshold to determine whether the outter boarder
        is slit (case 1) or air (case 2).
    rel_intensity_threshold_fov:
        the relative intensity threshold used to determine pixels within to the
        field of view, only valid for case 1.
    rel_intensity_threshold_sample:
        the relative intensity threshold used to determine pixels within the
        sample region, only valid for case 2, and the value is relative to the
        intensity of the air region (outter region in case 2).

    Returns
    -------
        The crop limits in (left, right, top, bottom) order.
    """
    # generate representative image
    if arrays.ndim == 2:
        img = arrays
    elif arrays.ndim == 3:
        img = arrays.mean(axis=0)
    else:
        raise ValueError("Only 2D and 3D arrays are supported.")

    # denoise
    img = median_filter(img, 9).astype(float)
    # rescale
    img = (img - img.min()) / (img.max() - img.min())
    # estimate background from four stripes near the border
    left = np.median(img[:, :border_pix])
    right = np.median(img[:, -border_pix:])
    top = np.median(img[:border_pix, :])
    bottom = np.median(img[-border_pix:, :])
    intensity_bg = np.median([left, right, top, bottom])

    if intensity_bg < rel_intensity_threshold_air_or_slit:
        # Case 1: slits in, i.e I_inner >> I_outer
        #     when the background intensity is around the bottom 5% of the
        #     total dynamic range, we select the pixels with the top 90% intensity
        #     to be the field of view.
        ys, xs = np.where(img > rel_intensity_threshold_fov)
        dx = dy = 0.0  # no expanding needed
    else:
        # Case 2: slits out, i.e I_inner < I_outer
        #     when the estimated background intensity is high (> 5%), we assume
        #     that the slits are either out or removed from image, therefore the
        #     detection now is for the object within the FOV.
        #     since object will absorb neutron, selecting the lower intensity
        #     region helps us identify the rough bounding box.
        ys, xs = np.where(img < intensity_bg * rel_intensity_threshold_sample)
        #
        width = xs.max() - xs.min()
        height = ys.max() - ys.min()
        #
        dx = width * expand_ratio
        dy = height * expand_ratio

    # return the limits
    return (
        int(max(xs.min() - dx, 0)),
        int(min(xs.max() + dx, img.shape[1])),
        int(max(ys.min() - dy, 0)),
        int(min(ys.max() + dy, img.shape[0])),
    )