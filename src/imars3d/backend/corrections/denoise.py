#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image noise reduction (denoise) module."""
import param
import multiprocessing
import numpy as np
import tomopy
import tomopy.util.mproc as mproc
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
from functools import partial
from scipy.signal import convolve2d
from scipy.ndimage import median_filter
from skimage.restoration import denoise_bilateral


logger = param.get_logger(__name__)
logger.name = __name__


def measure_noiseness(image: np.ndarray) -> float:
    """Measure the noiseness of the image.

    Reference paper, doi:`10.1006/cviu.1996.0060 <https://doi.org/10.1006/cviu.1996.0060>`_

    Parameters
    ----------
    image:
        The image to measure the noiseness of.

    Returns
    -------
        The noiseness of the image.
    """
    # rescale to [0, 255]
    image = (image - image.min()) / (image.max() - image.min()) * 255
    logger.debug(f"image range: [{image.min()}, {image.max()}]")
    # compute factor
    height, width = image.shape
    factor = np.sqrt(np.pi / 2.0) / (6 * (height - 2) * (width - 2))
    logger.debug(f"factor: {factor}")
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
    image:
        The image to measure the sharpness of.

    Returns
    -------
        The sharpness of the image.
    """
    # rescale to [0, 255]
    image = (image - image.min()) / (image.max() - image.min()) * 255
    logger.debug(f"image range: [{image.min()}, {image.max()}]")
    # compute gradient
    gx, gy = np.gradient(image)
    # use norm of gradient as approximation for sharpness
    return np.sqrt(np.square(gx) + np.square(gy)).mean()


def denoise_by_median(
    arrays: np.ndarray,
    median_filter_kernel: int = 3,
    max_workers: int = 0,
) -> np.ndarray:
    """
    Denoise the image stack with the median filter.

    Parameters
    ----------
    arrays:
        The image stack to denoise.
    median_filter_kernel:
        The kernel size of the median filter.
    max_workers:
        The number of cores to use for parallel processing, default is 0, which means using all available cores.

    Returns
    -------
        The denoised image stack.
    """
    if arrays.ndim == 2:
        logger.info("denoise completed via scipy's median filter")
        return median_filter(arrays, size=median_filter_kernel)
    elif arrays.ndim == 3:
        max_workers = None if max_workers == 0 else int(max_workers)
        logger.info("denoise completed via tomopy's median filter")
        return tomopy.misc.corr.median_filter(
            arrays,
            size=median_filter_kernel,
            ncore=max_workers,
        )
    else:
        raise ValueError(f"Unsupported image dimension: {arrays.ndim}")


def denoise_by_bilateral(
    arrays: np.ndarray,
    sigma_color: float = 0.02,
    sigma_spatial: float = 5.0,
    max_workers: int = 0,
) -> np.ndarray:
    """
    Denoise the image stack with the bilateral filter.

    Parameters
    ----------
    arrays:
        The image stack to denoise.
    sigma_color:
        Standard deviation for grayvalue/color distance (radiometric similarity).
    sigma_spatial:
        Standard deviation for range distance.
    max_workers:
        The number of cores to use for parallel processing, default is 0, which means using all available cores.

    Returns
    -------
        The denoised image stack.
    """
    # NOTE:
    #  The bilateral filter based denoise method can be contributed back to tomopy
    #  upstream.
    if arrays.ndim == 2:
        return denoise_by_bilateral_2d(arrays)
    elif arrays.ndim == 3:
        max_workers = mproc.mp.cpu_count() if max_workers == 0 else int(max_workers)
        with SharedMemoryManager() as smm:
            # create the shared memory
            shm = smm.SharedMemory(arrays.nbytes)
            # create a numpy array point to the shared memory
            shm_arrays = np.ndarray(
                arrays.shape,
                dtype=arrays.dtype,
                buffer=shm.buf,
            )
            # copy the data to the shared memory
            np.copyto(shm_arrays, arrays)
            # mp
            rst = process_map(
                partial(denoise_by_bilateral_2d, sigma_color=sigma_color, sigma_spatial=sigma_spatial),
                [img for img in shm_arrays],
                max_workers=max_workers,
                desc="denoise_by_bilateral",
            )
        logger.info("denoise completed via bilateral filter")
        return np.array(rst)
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
    array_2d:
        The image to denoise.
    sigma_color:
        Standard deviation for grayvalue/color distance (radiometric similarity).
    sigma_spatial:
        Standard deviation for range distance.

    Returns
    -------
        The denoised image.
    """
    # NOTE:
    # need to make this a separate function so as to pickle it with ProcessPoolExecutor
    array2d_max = array_2d.max()
    logger.debug(f"denoise_by_bilateral_2d:array2d_max = {array2d_max}")
    _sigma_color = sigma_color / array2d_max
    array_2d /= array2d_max
    array_2d = denoise_bilateral(array_2d, sigma_color=_sigma_color, sigma_spatial=sigma_spatial)
    logger.info(f"Denoise completed via bilateral filter (2D).")
    return array_2d * array2d_max


class denoise(param.ParameterizedFunction):
    """
    Denoise the image stack with the median filter.

    Parameters
    ----------
    arrays: np.ndarray
        The image stack to denoise.
    method: str = 'bilateral'
        The denoise method to use.
    median_filter_kernel: int = 3
        The kernel size of the median filter, only valid for 'median' method.
    bilateral_sigma_color: float = 0.02
        The sigma of the color/gray space, only valid for 'bilateral' method.
    bilateral_sigma_spatial: float = 5.
        The sigma of the spatial space, only valid for 'bilateral' method.
    max_workers: int = 0
        The number of cores to use for parallel processing, default is 0, which means using all available cores.

    Returns
    -------
        The denoised image stack.
    """

    arrays = param.Array(
        doc="The image stack to denoise.",
    )
    method = param.Selector(
        default="bilateral",
        objects=["median", "bilateral"],
        doc="The denoise method to use.",
    )
    median_filter_kernel = param.Integer(
        default=3,
        bounds=(3, None),
        doc="The kernel size of the median filter, only valid for 'median' method.",
    )
    bilateral_sigma_color = param.Number(
        default=0.02,
        bounds=(0.0, None),
        doc="The sigma of the color/gray space, only valid for 'bilateral' method.",
    )
    bilateral_sigma_spatial = param.Number(
        default=5.0,
        bounds=(0.0, None),
        doc="The sigma of the spatial space, only valid for 'bilateral' method.",
    )
    max_workers = param.Integer(
        default=0,
        bounds=(0, None),
        doc="The number of cores to use for parallel processing, default is 0, which means using all available cores.",
    )

    def __call__(self, **params):
        """Call the denoise function."""
        logger.info(f"Executing Filter: Denoise Filter")
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)

        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = multiprocessing.cpu_count() if params.max_workers <= 0 else params.max_workers
        logger.debug(f"max_worker={self.max_workers}")

        if params.method == "median":
            logger.info(f"Executing Filter: Denoise Filter with median filter")
            return denoise_by_median(
                arrays=params.arrays,
                median_filter_kernel=params.median_filter_kernel,
                max_workers=self.max_workers,
            )
        elif params.method == "bilateral":
            logger.info(f"Executing Filter: Denoise Filter with bilateral filter")
            return denoise_by_bilateral(
                arrays=params.arrays,
                bilateral_sigma_color=params.bilateral_sigma_color,
                bilateral_sigma_spatial=params.bilateral_sigma_spatial,
                max_workers=self.max_workers,
            )
        else:
            # NOTE:
            # param.Selector should have already checked this, but in case user
            # figure out a way to bypass param, let's double check here.
            raise ValueError(f"Unsupported denoise method: {params.method}")
