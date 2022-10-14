#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import param
import multiprocessing
import numpy as np
import tomopy.util.mproc as mproc
from typing import Tuple
from functools import partial
from scipy.optimize import minimize_scalar
from scipy.optimize import OptimizeResult
from skimage.transform import rotate
from skimage.registration import phase_cross_correlation
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map


logger = param.get_logger(__name__)
logger.name = __name__


def find_180_deg_pairs_idx(
    angles: np.ndarray,
    atol: float = 1e-3,
    in_degrees: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return the indices of the 180 degree pairs from given list of angles.

    Parameters
    ----------
    angles:
        The list of angles as a 1d array.
    atol:
        The absolute tolerance in degree for the 180 degree pairs.
    in_degrees:
        Whether the angles are in degrees or radians, default is in degrees.

    Returns
    -------
        The indices of the 180 degree pairs (low_range, high_range)
    """
    # ensure correct dimension
    if angles.ndim != 1:
        logger.error(f"angles.ndim = {angles.ndim}, expected 1")
        raise ValueError("angles must be a 1d array")
    # ensure angles are in degrees
    angles = angles if in_degrees else np.degrees(angles)
    # compute the self difference matrix
    angles = angles[..., np.newaxis]
    diff_matrix = angles.T - angles
    # find the indices of the 180 degree pairs
    idx_lowrange, idx_highrange = np.where(np.isclose(diff_matrix, 180, atol=atol))
    return idx_lowrange, idx_highrange


def calculate_shift(
    reference_image: np.ndarray,
    moving_image: np.ndarray,
) -> float:
    """
    Calculate the amount of shift needed to move the moving image to the
    reference image.
    This method requires the rotating object to be fully in the field of view.

    Parameters
    ----------
    reference_image:
        The reference image, often the radiograph taken at omega (< 180 deg)
    moving_image:
        The moving image, often the radiograph taken at omega + 180 deg

    Returns
    -------
        The amount of shift in pixels
    """
    # API documentation can be find at:
    # https://scikit-image.org/docs/stable/api/skimage.registration.html#skimage.registration.phase_cross_correlation
    shift = phase_cross_correlation(
        reference_image=reference_image,
        moving_image=np.fliplr(moving_image),
        upsample_factor=2.0,  # upsample by 2x for subpixel accuracy
    )
    # NOTE:
    # the content of shift contains
    # - shifts: ndarray, (vertical_shift, horizontal_shift)
    # - errors: float
    # - phasediff: float
    # here we only care about the horizontal shift
    logger.debug(f"calculate_shift.shift = {shift}")
    return shift[0][1]


def calculate_dissimilarity(
    tilt: float,
    image0: np.ndarray,
    image1: np.ndarray,
) -> float:
    """
    Calculate the p3-norm based dissimilarity between the two images at a given
    tilt angle (in degrees).

    Parameters
    ----------
    tilt:
        The tilt angle in degrees.
    image0:
        The first image for comparison, which is often the radiograph taken at
        omega (< 180 deg)
    image1:
        The second image for comparison, which is often the radiograph taken at
        omega + 180 deg

    Returns
    -------
        The p3-norm based dissimilarity between the two images

    NOTE
    ----
        1. The rotation of an image is carried out by scikit-image, which is using
        bilinear interpolation (order=1) by default. This introduces artifacts:
        the image is slightly distorted at a non-zero tilt angle, therefore
        perfect matching pairs with a tilted angles greater than 2.0 might return a non-zero dissimilarity.

        2. In case of non-centered rotation axis, the image cropped to ensure only
        both images have the object in the center of FOV, however this might fail
        if the object is partially out of the FOV in both images as the image
        registration does not work for two different partials of the same object.
    """
    # calculate the relative shift
    shift_val = calculate_shift(image0, image1)
    # crop both image to same range that contains the object
    # NOTE:
    #   1. if the shift is less than a pixel, the rotation center is basically at
    #      the center, therefore no need to crop
    #   2. DO NOT use shift from scipy.ndimage as it will distort the image by
    #      its implied interpolation.
    logger.debug(f"calculate_dissimilarity.shift_val = {shift_val}")
    if shift_val < -1.0:
        img0_tmp = image0[:, : int(shift_val)]
        img180_tmp = np.fliplr(image1)[:, -int(shift_val) :]
    elif shift_val > 1.0:
        img0_tmp = image0[:, int(shift_val) :]
        img180_tmp = np.fliplr(image1)[:, : -int(shift_val)]
    else:
        img0_tmp = image0
        img180_tmp = np.fliplr(image1)

    # normalize image
    img0_tmp = (img0_tmp - img0_tmp.min()) / (img0_tmp.max() - img0_tmp.min())
    img180_tmp = (img180_tmp - img180_tmp.min()) / (img180_tmp.max() - img180_tmp.min())

    # rotate
    # if the rotation axis is tilted by 2 deg, we need to tilt the image back by -2 deg
    img0_tmp = rotate(
        img0_tmp,
        -tilt,
        mode="edge",
        resize=True,
        preserve_range=True,
        order=1,  # use default bi-linear interpolation for rotation
    )
    # since 180 is flipped, tilting back -2 deg of the original img180 means tilting +2 deg
    # of the flipped one
    img180_tmp = rotate(
        img180_tmp,
        +tilt,
        mode="edge",
        resize=True,
        preserve_range=True,
        order=1,  # use default bi-linear interpolation for rotation
    )

    # p-norm
    # NOTE: p3 norm is selected as it makes the error function more sensitive
    #       around the minimum.
    diff = np.abs(img0_tmp - img180_tmp)
    err = np.power(diff, 3).sum() / (np.linalg.norm(img0_tmp) * np.linalg.norm(img180_tmp))
    logger.debug(f"calculate_dissimilarity.diff = {diff}")
    logger.debug(f"calculate_dissimilarity.err = {err}")

    # cleanup
    del img0_tmp, img180_tmp
    return err


def calculate_tilt(
    image0: np.ndarray,
    image180: np.ndarray,
    low_bound: float = -5.0,
    high_bound: float = 5.0,
) -> OptimizeResult:
    """
    Use optimization to find the in-plane tilt angle.

    Parameters
    ----------
    image0:
        The first image for comparison, which is often the radiograph taken at
        omega (< 180 deg)
    image180:
        The second image for comparison, which is often the radiograph taken at
        omega + 180 deg
    low_bound:
        The lower bound of the tilt angle search space
    high_bound:
        The upper bound of the tilt angle search space

    Returns
    -------
        The optimization results from scipy.optimize.minimize_scalar
    """
    # make the error function
    err_func = partial(calculate_dissimilarity, image0=image0, image1=image180)
    # use bounded uni-variable optimizer to locate the tilt angle that minimize
    # the dissimilarity of the 180 deg pair
    res = minimize_scalar(
        err_func,
        bounds=(low_bound, high_bound),
    )
    #
    logger.debug(f"calculate_tilt.res:\n{res}")
    return res


def tilt_correction(
    arrays: np.ndarray,
    omegas: np.ndarray,
    low_bound: float = -5.0,
    high_bound: float = 5.0,
    cut_off_angle_deg: float = 1e-3,
    ncore: int = -1,
):
    """
    Detect and correct the rotation axis tilt from the given radiograph stack.

    Parameters
    ----------
    arrays:
        The radiograph stack fro tilt correction
    omegas:
        The list of omega angles in radians (follow tomopy convention)
    low_bound:
        The lower bound of the tilt angle search space
    high_bound:
        The upper bound of the tilt angle search space
    cut_off_angle_deg:
        The angle in degrees to cut off the rotation axis tilt correction, i.e.
        skip applying tilt correction for tilt angles that are too small.
    ncore:
        Number of cores to use for parallel median filtering, default is -1,
        which means using all available cores.

    Returns
    -------
        The tilt corrected array
    """
    if arrays.ndim != 3:
        raise ValueError("arrays must be a 3d array")
    # step 1: find the 180 degree pairs
    idx_lowrange, idx_highrange = find_180_deg_pairs_idx(omegas, in_degrees=False)
    # step 2: calculate the tilt from each pair
    ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
    with SharedMemoryManager() as smm:
        # create shared memory
        shm = smm.SharedMemory(arrays.nbytes)
        shm_arrays = np.ndarray(arrays.shape, dtype=arrays.dtype, buffer=shm.buf)

        np.copyto(shm_arrays, arrays)

        rst = process_map(
            partial(calculate_tilt, low_bound=low_bound, high_bound=high_bound),
            [shm_arrays[il] for il in idx_lowrange],
            [shm_arrays[ih] for ih in idx_highrange],
            max_workers=ncore,
            desc="Calculating tilt correction",
        )
    # extract the tilt angles from the optimization results
    tilts = np.array([result.x for result in rst])
    # use the average of the found tilt angles
    tilt = np.mean(tilts)
    # step 3: apply the tilt correction
    if abs(tilt) < cut_off_angle_deg:
        return arrays
    else:
        return apply_tilt_correction(arrays, tilt, ncore)


def apply_tilt_correction(
    arrays: np.ndarray,
    tilt: float,
    ncore: int = -1,
) -> np.ndarray:
    """
    Apply the tilt correction to the given array.
    For a 2 deg tilted rotation axis, this function will rotate each image -2
    deg so that the rotation axis is upright.

    Parameters
    ----------
    arrays:
        The array for tilt correction
    tilt:
        The rotation axis tilt angle in degrees
    ncore:
        Number of cores to use for parallel median filtering, default is -1, which means using all available cores.

    Returns
    -------
        The tilt corrected array
    """
    # dimensionality check
    if arrays.ndim == 2:
        return rotate(arrays, -tilt, resize=False, preserve_range=True)
    elif arrays.ndim == 3:

        # NOTE: have to switch to threadpool as we are using a nested function
        ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
        with SharedMemoryManager() as smm:
            shm = smm.SharedMemory(arrays.nbytes)
            shm_arrays = np.ndarray(arrays.shape, dtype=arrays.dtype, buffer=shm.buf)
            np.copyto(shm_arrays, arrays)

            rst = process_map(
                partial(rotate, angle=-tilt, resize=False, preserve_range=True),
                [shm_arrays[idx] for idx in range(arrays.shape[0])],
                max_workers=ncore,
                desc="Applying tilt corr",
            )

        return np.array(rst)
    else:
        raise ValueError("array must be a 2d/3d array")
