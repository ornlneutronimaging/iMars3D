#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy


def normalization(
    arrays: np.ndarray,
    flats: np.ndarray,
    darks: np.ndarray,
    cut_off: float = -1.0,
    ncore: int = -1,
) -> np.ndarray:
    """
    Normalize the input array(s) by subtracting the dark field and dividing by the adjusted flat field.

    Parameters
    ----------
    arrays:
        3D array of images, the first dimension is the rotation angle omega.
    flats:
        3D array of flat field images (aka flat field, open beam), axis=0 is the image number axis.
    darks:
        3D array of dark field images, axis=0 is the image number axis.
    cut_off:
        Permitted maximum value for the normalized data, originated from tomopy, negative values means no cutoff.
    ncore:
        number of cores to use for parallel processing, default is -1, which means using all available cores.

    Returns
    -------
        normalized 3D array of images, the first dimension is the rotation angle omega.
    """
    # parse input (mostly for Tomopy)
    cut_off = None if cut_off < 0 else float(cut_off)
    ncore = None if ncore == -1 else int(ncore)
    # use median filter to remove outliers from flats and darks
    # NOTE: this will remove the random noises coming from the environment.
    flats = np.median(flats, axis=0)
    darks = np.median(darks, axis=0)
    # apply normalization
    # NOTE:
    # For pixels where dark > flat, tomopy replace the value with 1e-6 on-the-fly
    # see https://github.com/tomopy/tomopy/blob/master/source/tomopy/prep/normalize.py#L135
    #
    arrays_normalized = tomopy.normalize(arrays, flats, darks, cutoff=cut_off, ncore=ncore)
    # return
    return arrays_normalized
