#!/usr/bin/env python3
import numpy as np
import tomopy


def normalization(
    arrays: np.ndarray,
    whites: np.ndarray,
    darks: np.ndarray,
    cut_off: float = -1.0,
    ncore: int = -1,
) -> np.ndarray:
    """
    Normalize the input array(s) by subtracting the dark field and dividing by the adjusted white field.

    Parameters
    ----------
    @param arrays: 3D array of images, the first dimension is the rotation angle omega.
    @param whites: 3D array of white field images (aka flat field, open beam), axis=0 is the image number axis.
    @param darks: 3D array of dark field images, axis=0 is the image number axis.
    @param cut_off: Permitted maximum value for the normalized data, originated from tomopy, negative values means no cutoff.
    @param ncore: number of cores to use for parallel processing, default is -1, which means using all available cores.

    Returns
    -------
    @return: normalized 3D array of images, the first dimension is the rotation angle omega.
    """
    # parse input (mostly for Tomopy)
    cut_off = None if cut_off < 0 else float(cut_off)
    ncore = None if ncore == -1 else ncore
    # use median filter to remove outliers from whites and darks
    # NOTE: this will remove the random noises coming from the environment.
    whites = np.median(whites, axis=0)
    darks = np.median(darks, axis=0)
    # apply normalization
    # NOTE:
    # For pixels where dark > white, tomopy replace the value with 1e-6 on-the-fly
    # see https://github.com/tomopy/tomopy/blob/master/source/tomopy/prep/normalize.py#L135
    #
    arrays_normalized = tomopy.normalize(arrays, whites, darks, cutoff=cut_off, ncore=ncore)
    # return
    return arrays_normalized
