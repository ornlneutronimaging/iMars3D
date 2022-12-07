#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iMars3D normalization module."""

# package imports
from imars3d.backend.util.functions import clamp_max_workers

# third party imports
import numpy as np
import param
from tomopy.prep.normalize import minus_log as tm_minus_log

# standard imports
import logging


logger = logging.getLogger(__name__)


class normalization(param.ParameterizedFunction):
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
    max_workers:
        number of cores to use for parallel processing, default is 0, which means using all available cores.

    Returns
    -------
        normalized 3D array of images, the first dimension is the rotation angle omega.
    """

    arrays = param.Array(doc="3D array of images, the first dimension is the rotation angle omega.", default=None)
    flats = param.Array(
        doc="3D array of flat field images (aka flat field, open beam), axis=0 is the image number axis.", default=None
    )
    darks = param.Array(doc="3D array of dark field images, axis=0 is the image number axis.", default=None)
    max_workers = param.Integer(
        default=0,
        bounds=(0, None),
        doc="Maximum number of processes allowed during execution",
    )

    def __call__(self, **params):
        """Perform normalization via numpy."""
        logger.info("Executing Filter: Normalization")
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)
        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = clamp_max_workers(params.max_workers)
        logger.debug(f"max_worker={self.max_workers}")

        # use median filter to remove outliers from flats and darks
        # NOTE: this will remove the random noises coming from the environment.
        self.flats = np.median(params.flats, axis=0)
        self.darks = np.median(params.darks, axis=0)
        # apply normalization
        _bg = self.flats - self.darks
        _bg[_bg <= 0] = 1e-6
        params.arrays = params.arrays - self.darks
        arrays_normalized = np.true_divide(params.arrays, _bg, dtype=np.float32)

        # return
        logger.info("FINISHED Executing Filter: Normalization")

        return arrays_normalized


class minus_log(param.ParameterizedFunction):
    r"""Computation of the minus natural log of a given array.

    Calls `tomopy.prep.normalize.minus_log`.

    Parameters
    ----------
    arrays : np.ndarray
        any multidimensional array with values greater than one.

    max_workers : int
        number of cores to use for parallel processing, default is 0, which means using all available cores.

    Returns
    -------
        np.ndarray

    Raises
    ------
    ValueError
        Any entry in the input array is equal or smaller than zero
    """

    arrays = param.Array(doc="any multidimensional array with values greater than one.", default=None)
    max_workers = param.Integer(
        default=0,
        bounds=(0, None),
        doc="Maximum number of processes allowed during execution",
    )

    def __call__(self, **params):
        """Perform minus_log via tomopy."""
        logger.info("Executing Filter: minus_log")
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)
        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = clamp_max_workers(params.max_workers)
        logger.debug(f"max_worker={self.max_workers}")
        if not np.all(params.arrays > 0.0):
            raise ValueError("'minus_log' cannot be applied to arrays containing elements equal or smaller than zero")
        arrays_normalized = tm_minus_log(params.arrays, ncore=self.max_workers)
        logger.info("FINISHED Executing Filter: minus_log")
        return arrays_normalized
