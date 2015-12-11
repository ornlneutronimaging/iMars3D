#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for image filters.
"""

from __future__ import absolute_import, division, print_function

import numpy as np

import logging
logger = logging.getLogger(__name__)


__author__ = "Doga Gursoy"
__copyright__ = "Copyright (c) 2015, ORNL."
__docformat__ = 'restructuredtext en'
__all__ = ['gamma_filter',
           'remove_outliers']


def gamma_filter(img, threshold=None):
    """
    Performs gamma filtering on a given image.

    Parameters
    ----------
    img : ndarray
        2D image.
    threshold : float
        Threshold for detecting outliers.

    Returns
    -------
    ndarray
        Filtered 2D image.
    """
    if threshold is None:
        threshold = np.iinfo(img.dtype).max() / 2.
    return remove_outliers_bymedian(img, img > threshold)


def remove_outliers(img, ind, size=5):
    """
    Remove outliers from the given image using a local
    median filtering around the outliers.

    Parameters
    ----------
    img : ndarray
        2D image.
    ind : ndarray of ints
        Pixel indexes of outliers.
    size : int, optional
        Size of the median filter.

    Returns
    -------
    ndarray
       Corrected array.
    """
    half = size // 2
    img[ind] = np.nan
    indexes = np.where(img != img)
    for ind1, ind2 in zip(*indexes):
        img[ind1, ind2] = np.nanmedian(
            img[max(ind1-half, 0):ind1+half+1, max(ind2-half, 0):ind2+half+1])
        continue
    return img
