#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Imaging correction for beam hardening."""
import logging
import param
import numpy as np
from imars3d.backend.util.functions import clamp_max_workers, calculate_chunksize
from multiprocessing.managers import SharedMemoryManager
from functools import partial
from tqdm.contrib.concurrent import process_map
from algotom.prep.correction import beam_hardening_correction as algotom_beam_hardening_correction

logger = logging.getLogger(__name__)


class beam_hardening_correction(param.ParameterizedFunction):
    """Imaging correction for beam hardening.

    Parameters
    ----------
    arrays: np.ndarray
        The image stack to be corrected for beam hardening, must be normalized to 0-1.
    q: float
        The beam hardening correction parameter, must be positive.
    n: float
        The beam hardening correction parameter, must be greater than 1.
    opt: bool
        If True, correction biased towards 1.0, else correction biased towards 0.0.
    max_workers: int
        The maximum number of workers to use for parallel processing.
    tqdm_class: panel.widgets.Tqdm
        Class to be used for rendering tqdm progress

    Returns
    -------
    np.ndarray
        The corrected image stack.
    """

    arrays = param.Array(
        doc="The image stack to be corrected for beam hardening, must be normalized to 0-1.",
        default=None,
    )
    q = param.Number(
        doc="The beam hardening correction parameter.",
        default=0.005,
        bounds=(0, None),
    )
    n = param.Number(
        doc="The beam hardening correction parameter.",
        default=20.0,
        bounds=(1, None),
    )
    opt = param.Boolean(
        doc="If True, correction biased towards 1.0, else correction biased towards 0.0.",
        default=True,
    )
    max_workers = param.Integer(
        doc="The maximum number of workers to use for parallel processing, default is 0, which means using all available cores.",
        default=0,
        bounds=(0, None),
    )
    tqdm_class = param.ClassSelector(class_=object, doc="Progress bar to render with")

    def __call__(self, **params):
        """Perform the beam hardening correction."""
        logger.info("Performing beam hardening correction.")
        # type check & bounds check
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)
        # set max_workers
        self.max_workers = clamp_max_workers(params.max_workers)
        logger.debug(f"max_worker={self.max_workers}")

        if params.arrays.ndim == 2:
            return algotom_beam_hardening_correction(params.arrays, params.q, params.n, params.opt)
        elif params.arrays.ndim == 3:
            with SharedMemoryManager() as smm:
                shm = smm.SharedMemory(params.arrays.nbytes)
                shm_arrays = np.ndarray(params.arrays.shape, dtype=params.arrays.dtype, buffer=shm.buf)
                np.copyto(shm_arrays, params.arrays)
                # mp
                kwargs = {
                    "max_workers": self.max_workers,
                    "chunksize": calculate_chunksize(params.arrays.shape[0], self.max_workers),
                    "desc": "denoise_by_bilateral",
                }
                if self.tqdm_class:
                    kwargs["tqdm_class"] = self.tqdm_class
                rst = process_map(
                    partial(algotom_beam_hardening_correction, q=params.q, n=params.n, opt=params.opt),
                    [shm_arrays[i] for i in range(shm_arrays.shape[0])],
                    **kwargs,
                )
                return np.array(rst)
        else:
            raise ValueError("The input array must be either 2D or 3D.")
