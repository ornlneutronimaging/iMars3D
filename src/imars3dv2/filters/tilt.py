#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from functools import partial
from scipy.optimize import minimize_scalar
from skimage.transform import rotate
from skimage.registration import phase_cross_correlation


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
    #
    shift = phase_cross_correlation(
        reference_image=reference_image,
        moving_image=np.fliplr(moving_image),
        upsample_factor=2.0,
    )
    #
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
       bilinear interpolation (order=1) by default. This introduces the following
       artifacts:
         - The image is slightly distorted at a non-zero tilt angle, therefore
           perfect matching pairs with a tilted angles greater than 2.0 might
           return a non-zero dissimilarity.
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
        order=1,  # use default bi-linear interpolation for rotation
    )
    # since 180 is flipped, tilting back -2 deg of the original img180 means tilting +2 deg
    # of the flipped one
    img180_tmp = rotate(
        img180_tmp,
        +tilt,
        mode="edge",
        resize=True,
        order=1,  # use default bi-linear interpolation for rotation
    )

    # p-norm
    diff = np.abs(img0_tmp - img180_tmp)
    err = np.power(diff, 3).sum() / (np.linalg.norm(img0_tmp) * np.linalg.norm(img180_tmp))
    return err


def calculate_tilt(
    image0: np.ndarray,
    image180: np.ndarray,
    low_bound: float = -5.0,
    high_bound: float = -5.0,
) -> float:
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
        The in-plane tilt angle in degrees
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
    return res.x
