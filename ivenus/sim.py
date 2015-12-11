#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for simulating images.
"""

from __future__ import absolute_import, division, print_function

import numpy as np

import logging
logger = logging.getLogger(__name__)


__author__ = "Doga Gursoy"
__copyright__ = "Copyright (c) 2015, ORNL."
__docformat__ = 'restructuredtext en'
__all__ = ['get_random_bg',
           'add_random_outlier']


def get_random_bg(xsize, ysize, mean=0., std=1.):
    """
    Return a random image of given size with values
    fluctating around a given mean value.

    Parameters
    ----------
    xsize : int
        Size of image on x-axis.
    ysize : int
        Size of image on y-axis.
    mean : float, optional
        Mean of the pixel values in the final image.
    std : float, optional
        Standard deviation of the pixel values in
        the final image.

    Returns
    -------
    ndarray
        2D random image.
    """
    return np.random.randn(xsize, ysize) * std + mean


def add_random_outlier(img, num_out, mean=0., std=10.):
    """
    Return image with added shot noise. It adds N random
    outliers into the image with values fluctating
    around the given center value.

    Parameters
    ----------
    img : float
        2D numpy array.
    num_out : int
        Number of outliers to be added to the image.
    mean : float, optional
        Mean of the pixel values in the final image.
    std : float, optional
        Standard deviation of the pixel values in
        the final image.

    Returns
    -------
    ndarray
        2D random image with added shot noise.
    """
    indices = np.random.random_integers(0, img.size, num_out)
    saved = img.shape  # What is this for?
    img.shape = -1
    img[indices] = np.random.randn(num_out) * std + mean
    img.shape = saved
    return img
