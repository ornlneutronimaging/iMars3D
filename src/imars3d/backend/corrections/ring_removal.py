#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iMars3D's ring artifact correction module."""
import logging
import param
from imars3d.backend.util.functions import clamp_max_workers
import scipy
import numpy as np

try:
    import bm3d_streak_removal as bm3dsr
except ImportError:
    # add a log?
    bm3dsr = None
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
from functools import partial

logger = logging.getLogger(__name__)


class bm3d_ring_removal(param.ParameterizedFunction):
    """
    Remove ring artifact from sinograms using BM3D method.

    ref: `10.1107/S1600577521001910 <http://doi.org/10.1107/S1600577521001910>`_

    Parameters
    ----------
    arrays: np.ndarray
        Input radiograph stack.

    Returns
    -------
        Radiograph stack with ring artifact removed.

    Notes
    -----
    1. The parallel processing is handled at the bm3d level, and it is an intrinsic
    slow correction algorithm running on CPU.
    2. The underlying BM3D library uses stdout to print progress instead of a progress
    bar.
    """

    arrays = param.Array(doc="Input radiograph stack.", default=None)
    # parameters passed to bm3dsr.extreme_streak_attenuation
    extreme_streak_iterations = param.Integer(default=3, doc="Number of iterations for extreme streak attenuation.")
    extreme_detect_lambda = param.Number(
        default=4.0,
        doc="Consider streaks which are stronger than lambda * local_std as extreme.",
    )
    extreme_detect_size = param.Integer(
        default=9,
        doc="Half window size for extreme streak detection -- total (2*s + 1).",
    )
    extreme_replace_size = param.Integer(
        default=2,
        doc="Half window size for extreme streak replacement -- total (2*s + 1).",
    )
    # parameters passed to bm3dsr.multiscale_streak_removal
    max_bin_iter_horizontal = param.Integer(
        default=0,
        doc="The number of total horizontal scales (counting the full scale).",
        bounds=(0, None),
    )
    bin_vertical = param.Integer(
        default=0,
        doc="The factor of vertical binning, e.g. bin_vertical=32 would perform denoising in 1/32th of the original vertical size.",
        bounds=(0, None),
    )
    filter_strength = param.Number(
        default=1.0,
        doc="Strength of BM4D denoising (>0), where 1 is the standard application, >1 is stronger, and <1 is weaker.",
        bounds=(0, None),
    )
    use_slices = param.Boolean(
        default=True,
        doc="If True, the sinograms will be split horizontally across each binning iteration into overlapping.",
    )
    slice_sizes = param.List(
        default=None,
        doc="A list of horizontal sizes for use of the slicing if use_slices=True. By default, slice size is either 39 pixels or 1/5th of the total width of the current iteration, whichever is larger.",
    )
    slice_step_sizes = param.List(
        default=None,
        doc="List of number of pixels between slices obtained with use_slices=True, one for each binning iteration. By default 1/4th of the corresponding slice size.",
    )
    denoise_indices = param.List(
        default=None,
        doc="Indices of sinograms to denoise; by default, denoises the full stack provided.",
    )
    # note: we are skipping the bm3d_profile_obj parameter as bm3d is not explicitly used in iMars3D.

    def __call__(self, **params):
        """See class level documentation for help."""
        if not bm3dsr:
            logger.warning("something informative")
            raise RuntimeError("probably same as warning")
        else:
            logger.info("Executing Filter: Remove Ring Artifact with BM3D")
        _ = self.instance(**params)
        params = param.ParamOverrides(self, params)
        # mangle parameters
        if params.max_bin_iter_horizontal == 0:
            params.max_bin_iter_horizontal = "auto"
        if params.bin_vertical == 0:
            params.bin_vertical = "auto"
        # step 1: extreme streak attenuation
        logger.debug("Perform extreme streak attenuation")
        param.arrays = bm3dsr.extreme_streak_attenuation(
            data=params.arrays,
            extreme_streak_iterations=params.extreme_streak_iterations,
            extreme_detect_lambda=params.extreme_detect_lambda,
            extreme_detect_size=params.extreme_detect_size,
            extreme_replace_size=params.extreme_replace_size,
        )
        # step 2: multiscale streak removal
        logger.debug("Perform multiscale streak removal")
        param.arrays = bm3dsr.multiscale_streak_removal(
            data=params.arrays,
            max_bin_iter_horizontal=params.max_bin_iter_horizontal,
            bin_vertical=params.bin_vertical,
            filter_strength=params.filter_strength,
            use_slices=params.use_slices,
            slice_sizes=params.slice_sizes,
            slice_step_sizes=params.slice_step_sizes,
            denoise_indices=params.denoise_indices,
        )
        logger.info("FINISHED Executing Filter: Remove Ring Artifact")
        return param.arrays


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
    tqdm_class: imars3d.ui.widgets.TqdmType
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
        """See class level documentation for help."""
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
        """See class level documentation for help."""
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
