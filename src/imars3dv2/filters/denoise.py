#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy
import tomopy.util.mproc as mproc
import concurrent.futures as cf
from scipy.signal import convolve2d
from scipy.ndimage import median_filter
from skimage.restoration import denoise_bilateral


def measure_noiseness(image: np.ndarray) -> float:
    """
    Measure the noiseness of the image, doi:10.1006/cviu.1996.0060

    Parameters
    ----------
    @param image:
        The image to measure the noiseness of.

    Returns
    -------
    @return:
        The noiseness of the image.
    """
    # rescale to [0, 255]
    image = (image - image.min()) / (image.max() - image.min()) * 255
    # compute factor
    height, width = image.shape
    factor = np.sqrt(np.pi / 2.0) / (6 * (height - 2) * (width - 2))
    # set kernel
    kernel = np.array(
        [
            [1, -2, 1],
            [-2, 4, -2],
            [1, -2, 1],
        ]
    )
    # compute
    sigma = np.sum(np.sum(np.absolute(convolve2d(image, kernel))))
    return factor * sigma


def measure_sharpness(image: np.ndarray) -> float:
    """
    Measure the sharpness of the image, using norm of gradient as approximation.

    Parameters
    ----------
    @param image:
        The image to measure the sharpness of.

    Returns
    -------
    @return:
        The sharpness of the image.
    """
    # rescale to [0, 255]
    image = (image - image.min()) / (image.max() - image.min()) * 255
    # compute gradient
    gx, gy = np.gradient(image)
    # use norm of gradient as approximation for sharpness
    return np.sqrt(gx ** 2 + gy ** 2).mean()


def denoise(
    arrays: np.ndarray,
    method: str = "bilateral",
    median_filter_kernel: int = 3,
    bilateral_sigma_color: float = 0.02,
    bilateral_sigma_spatial: float = 5,
    ncore: int = -1,
) -> np.ndarray:
    """
    Denoise the image stack with the specified method.

    Parameters
    ----------
    @param arrays:
        The image stack to denoise.
    @param method:
        The denoise method to use.
    @param median_filter_kernel:
        The kernel size of the median filter, only valid for 'median' method.
    @param bilateral_sigma_color:
        The sigma of the color/gray space, only valid for 'bilateral' method.
    @param bilateral_sigma_spatial:
        The sigma of the spatial space, only valid for 'bilateral' method.
    @param ncore:
        The number of cores to use for parallel processing, default is -1, which means using all available cores.

    Returns
    -------
    @return:
        The denoised image stack.
    """
    if method == "median":
        return denoise_by_median(arrays, median_filter_kernel, ncore=ncore)
    elif method == "bilateral":
        return denoise_by_bilateral(arrays, bilateral_sigma_color, bilateral_sigma_spatial, ncore=ncore)
    else:
        raise ValueError("Unknown denoise method: {}".format(method))


def denoise_by_median(
    arrays: np.ndarray,
    median_filter_kernel: int = 3,
    ncore: int = -1,
) -> np.ndarray:
    """
    Denoise the image stack with the median filter.

    Parameters
    ----------
    @param arrays:
        The image stack to denoise.
    @param median_filter_kernel:
        The kernel size of the median filter.
    @param ncore:
        The number of cores to use for parallel processing, default is -1, which means using all available cores.

    Returns
    -------
    @return:
        The denoised image stack.
    """
    if arrays.ndim == 2:
        return median_filter(arrays, size=median_filter_kernel)
    elif arrays.ndim == 3:
        ncore = None if ncore == -1 else int(ncore)
        return tomopy.misc.corr.median_filter(
            arrays,
            size=median_filter_kernel,
            ncore=ncore,
        )
    else:
        raise ValueError("Unsupported image dimension: {}".format(arrays.ndim))


def denoise_by_bilateral(
    arrays: np.ndarray,
    sigma_color: float = 0.02,
    sigma_spatial: float = 5.0,
    ncore: int = -1,
):
    """
    Denoise the image stack with the bilateral filter.

    Parameters
    ----------
    @param arrays:
        The image stack to denoise.
    @param sigma_color:
        Standard deviation for grayvalue/color distance (radiometric similarity).
    @param sigma_spatial:
        Standard deviation for range distance.
    @param ncore:
        The number of cores to use for parallel processing, default is -1, which means using all available cores.

    Returns
    -------
    @return:
        The denoised image stack.
    """
    # NOTE:
    #  The bilateral filter based denoise method can be contributed back to tompy
    #  upstream.
    if arrays.ndim == 2:
        return denoise_by_bilateral_2d(arrays)
    elif arrays.ndim == 3:
        ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
        with cf.ProcessPoolExecutor(ncore) as e:
            jobs = [e.submit(denoise_by_bilateral_2d, array, sigma_color, sigma_spatial) for array in arrays]
        results = [job.result() for job in jobs]
        return np.array(results)
    else:
        raise ValueError("Unsupported image dimension: {}".format(arrays.ndim))


def denoise_by_bilateral_2d(
    array_2d: np.ndarray,
    sigma_color: float = 0.02,
    sigma_spatial: float = 5.0,
) -> np.ndarray:
    """
    Denoise an image with the bilateral filter.

    Parameters
    ----------
    @param array_2d:
        The image to denoise.
    @param sigma_color:
        Standard deviation for grayvalue/color distance (radiometric similarity).
    @param sigma_spatial:
        Standard deviation for range distance.

    Returns
    -------
    @return:
        The denoised image.
    """
    # NOTE:
    # need to make this a separate function so as to pickle it with ProcessPoolExecutor
    array2d_max = array_2d.max()
    _sigma_color = sigma_color / array2d_max
    array_2d /= array2d_max
    array_2d = denoise_bilateral(array_2d, sigma_color=_sigma_color, sigma_spatial=sigma_spatial)
    return array_2d * array2d_max
