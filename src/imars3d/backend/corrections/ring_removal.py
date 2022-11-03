#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iMars3D's ring artifact correction module."""
import logging
import param
import multiprocessing
from imars3d.backend.util.functions import clamp_max_workers
import scipy
import numpy as np
import tomopy.util.mproc as mproc
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
from functools import partial

logger = logging.getLogger(__name__)


class remove_ring_artifact(param.ParameterizedFunction):
    """
    Remove ring artifact from radiograph stack using Ketcham method.

    ref: `10.1117/12.680939 <https://doi.org/10.1117/12.680939>`_

    Parameters
    ----------
    arrays: np.ndarray
        Input radiograph stack.
    kernel_size: int = 5
        The size of the kernel (moving window) during local smoothing with median filter.
    sub_division: int = 10
        Sub-dividing the sinogram into subsections (along rotation angle axis).
    correction_range: tuple = (0.9, 1.1)
        Multiplicative correction factor is capped within given range.
    max_workers: int = 0
        Number of cores to use for parallel processing.
    tqdm_class:
        Class to be used for rendering tqdm progress

    Returns
    -------
        Radiograph stack with ring artifact removed.
    """

    arrays = param.Array(doc="Input radiograph stack.", default=None)
    kernel_size = param.Integer(
        default=5, doc="The size of the kernel (moving window) during local smoothing with median filter."
    )
    sub_division = param.Integer(
        default=10, doc="Sub-dividing the sinogram into subsections (along rotation angle axis)."
    )
    correction_range = param.List(
        default=[0.9, 1.1], doc="Multiplicative correction factor is capped within given range."
    )
    max_workers = param.Integer(default=0, bounds=(0, None), doc="Number of cores to use for parallel processing.")
    tqdm_class = param.ClassSelector(class_=object, doc="Progress bar to render with")

    def __call__(self, **params):
        logger.info("Executing Filter: Remove Ring Artifact")
        _ = self.instance(**params)
        params = param.ParamOverrides(self, params)
        val = self._remove_ring_artifact(
            params.arrays,
            params.kernel_size,
            params.sub_division,
            params.correction_range,
            params.max_workers,
            params.tqdm_class,
        )
        logger.info("FINISHED Executing Filter: Remove Ring Artifact")
        return val

    def _remove_ring_artifact(
        self,
        arrays: np.ndarray,
        kernel_size: int,
        sub_division: int,
        correction_range: tuple,
        max_workers: int,
        tqdm_class,
    ) -> np.ndarray:

        # sanity check
        if arrays.ndim != 3:
            raise ValueError("This correction can only be used for a stack, i.e. a 3D image.")
        # NOTE:
        # additional work is needed to avoid duplicating arrays in memory
        max_workers = clamp_max_workers(max_workers)
        # use shared memory to reduce memory footprint
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
            # invoke mp via tqdm wrapper
            kwargs = {
                "max_workers": max_workers,
                "desc": "Removing ring artifact",
            }
            if tqdm_class:
                kwargs["tqdm_class"] = tqdm_class
            rst = process_map(
                partial(
                    _remove_ring_artifact_Ketcham,
                    kernel_size=kernel_size,
                    sub_division=sub_division,
                    correction_range=correction_range,
                ),
                [shm_arrays[:, sino_idx, :] for sino_idx in range(shm_arrays.shape[1])],
                **kwargs
            )
        rst = np.array(rst)
        for i in range(arrays.shape[1]):
            arrays[:, i, :] = rst[i]
        return arrays


class remove_ring_artifact_Ketcham(param.ParameterizedFunction):
    """Ketcham's ring artifact removal method.

    Use the Ketcham method (doi:`10.1117/12.680939 <https://doi.org/10.1117/12.680939>`_)
    to remove ring artifact from given sinogram.

    Parameters
    ----------
    sinogram: np.ndarray
        Input sinogram.
    kernel_size: int = 5
        The size of the kernel (moving window) during local smoothing via median filter.
    sub_division: int = 10
        Sub-dividing the sinogram into subsections (along rotation angle axis).
    correction_range: tuple = (0.9, 1.1)
        Multiplicative correction factor is capped within given range.

    Returns
    -------
        Sinogram with ring artifact removed.

    NOTE
    ----
        0. The ring artifact refers to the halo type artifacts present in the final reconstruction results, which is often caused by local detector/pixel gain error during measurement.
        1. This method can only be used on a single sinogram.
        2. This method is assuming the ring artifact is of multiplicative nature, i.e. measured = signal * error.
    """

    sinogram = param.Array(doc="Input sinogram.", default=None)
    kernel_size = param.Integer(
        default=5, doc="The size of the kernel (moving window) during local smoothing via median filter."
    )
    sub_division = param.Integer(
        default=10, doc="Sub-dividing the sinogram into subsections (along rotation angle axis)."
    )
    correction_range = param.Tuple(
        default=(0.9, 1.1), doc="Multiplicative correction factor is capped within given range."
    )

    def __call__(self, **params):
        logger.info("Executing Filter: Remove Ring Artifact (Ketcham)")
        _ = self.instance(**params)
        params = param.ParamOverrides(self, params)
        val = _remove_ring_artifact_Ketcham(
            params.sinogram, params.kernel_size, params.sub_division, params.correction_range
        )
        logger.info("FINISHED Executing Filter: Remove Ring Artifact (Ketcham)")
        return val


def _remove_ring_artifact_Ketcham(
    sinogram: np.ndarray,
    kernel_size: int = 5,
    sub_division: int = 10,
    correction_range: tuple = (0.9, 1.1),
) -> np.ndarray:
    # sanity check
    if sinogram.ndim != 2:
        raise ValueError("This correction can only be used for a sinogram, i.e. a 2D image.")
    # sub-divide the sinogram into smaller sections
    edges = np.linspace(0, sinogram.shape[0], sub_division + 1).astype(int)
    #
    corr_ratios = []
    for bottom, top in zip(edges[:-1], edges[1:]):
        sub_sinogram = sinogram[bottom:top]
        sum_over_angle = sub_sinogram.sum(axis=0)
        # avoid divide by zero issue when dealing with emission type sinogram
        sum_over_angle = np.where(sum_over_angle == 0, 1.0, sum_over_angle)
        sum_over_angle_smoothed = scipy.signal.medfilt(sum_over_angle, kernel_size)
        # identify regions where large local variation occurs
        # - skip one window/kernel on both end (mostly air anyway)
        # - correction ratio is capped within specified range
        corr_ratio = np.ones_like(sum_over_angle)
        corr_ratio[kernel_size:-kernel_size] = (sum_over_angle_smoothed / sum_over_angle)[kernel_size:-kernel_size]
        corr_ratio[corr_ratio < correction_range[0]] = correction_range[0]
        corr_ratio[corr_ratio > correction_range[1]] = correction_range[1]
        #
        corr_ratios.append(corr_ratio)
    # use median to select the most probable correction ratio from all sub-sinograms
    corr_raio = np.median(corr_ratios, axis=0)
    return sinogram * corr_raio[np.newaxis, :]
