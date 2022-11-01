#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iMars3D: gamma filter module."""
import logging
import param
from imars3d.backend.util.functions import clamp_max_workers
import multiprocessing
import numpy as np
import tomopy


logger = logging.getLogger(__name__)


class gamma_filter(param.ParameterizedFunction):
    """Gamma filter.

    Replace near saturated pixels (due to gamma radiation) with median values.
    The median filtering is carried out by tomopy.remove_outlier.
    If selective median filtering is enabled (default), only the pixels greater than the specified threshold are replaced.

    Parameters
    ----------
    arrays: np.ndarray
        3D array of images, the first dimension is the rotation angle omega
    threshold: int = -1
        threshold for saturation, default is -1, which means using the internally defined threshold (see source code)
    median_kernel: int = 5
        size of the median filter kernel, default is 5
    axis: int = 0
        axis along which to chunk the array for parallel median filtering, default is 0.
    max_workers: int = 0
        number of cores to use for parallel median filtering, default is 0, which means using all available cores.
    selective_median_filter: bool = True
        whether to use selective median filtering, default is True.
    diff_tomopy: float = -1
        threshold passed to tomopy for median filter based outlier detection. Negative values will use the internal default value (see source code).

    Returns
    -------
    np.ndarray
        corrected 3D array of images, the first dimension is the rotation angle omega
    """

    arrays = param.Array(doc="3D array of images, the first dimension is the rotation angle omega", default=None)
    threshold = param.Integer(
        default=-1,
        doc="threshold for saturation, default is -1, which means using the internally defined threshold (see source code)",
    )
    median_kernel = param.Integer(
        default=5,
        bounds=(3, None),
        doc="size of the median filter kernel, default is 5",
    )
    axis = param.Integer(
        default=0,
        bounds=(0, 2),
        doc="axis along which to chunk the array for parallel median filtering, default is 0.",
    )
    max_workers = param.Integer(
        default=0,
        bounds=(0, None),
        doc="Maximum number of processes allowed during processing",
    )
    selective_median_filter = param.Boolean(
        default=True,
        doc="whether to use selective median filtering, default is True.",
    )
    diff_tomopy = param.Number(
        default=-1,
        doc="threshold passed to tomopy for median filter based outlier detection. Negative values will use the internal default value (see source code).",
    )

    def __call__(self, **params):
        """Replace near saturated pixels (due to gamma radiation) with median values."""
        logger.info("Executing Filter: Gamma Filter")
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)

        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = clamp_max_workers(params.max_workers)
        logger.debug("max_worker={self.max_workers}")

        # NOTE:
        # gamma_filter is intended to screen out over-saturated pixels, which are caused by gamma radiation.
        # so it should be used on images of counts that tied to the camera's dynamic range.
        # if the data is accidentally converted to float, we will assume that the the supposed dynamic range
        # is still for unit16.
        try:
            saturation_intensity = np.iinfo(params.arrays.dtype).max
        except ValueError:
            logger.warning("Switch to use standard uint16 threshold as given arrays are float type.")
            saturation_intensity = 65535
        threshold = saturation_intensity - 5 if params.threshold == -1 else params.threshold
        logger.debug(f"threshold={threshold}")

        # NOTE: use 20% of the total dynamic range as the outlier detection criterion
        diff_tomopy = 0.2 * saturation_intensity if params.diff_tomopy < 0.0 else params.diff_tomopy
        logger.debug(f"diff_tomopy={diff_tomopy}")
        # median filtering
        arrays_filtered = tomopy.remove_outlier(
            params.arrays,
            dif=diff_tomopy,
            size=params.median_kernel,
            axis=params.axis,
            ncore=self.max_workers,
        )
        logger.debug(f"arrays_filtered.shape={arrays_filtered.shape}")

        # selective replacement
        if params.selective_median_filter:
            logger.debug("use selective median filtering")
            arrays_filtered = np.where(
                params.arrays > threshold,
                arrays_filtered,
                params.arrays,
            )
        logger.debug(f"arrays_selective_filtered.shape={arrays_filtered.shape}")

        #
        logger.info("FINISHED Executing Filter: Gamma Filter")
        return arrays_filtered
