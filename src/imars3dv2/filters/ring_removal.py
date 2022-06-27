#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import scipy
import numpy as np
import tomopy.util.mproc as mproc
import concurrent.futures as cf


def remove_ring_artifact(
    arrays: np.ndarray,
    kernel_size: int = 5,
    sub_division: int = 10,
    correction_range: tuple = (0.9, 1.1),
    ncore: int = -1,
) -> np.ndarray:
    """
    Remove ring artifact from radiograph stack using Ketcham method.
    ref: `10.1117/12.680939 <https://doi.org/10.1117/12.680939>`_

    Parameters
    ----------
    @param arrays:
        Input radiograph stack.
    @param kernel_size:
        The size of the kernel (moving window) during local smoothing with median filter.
    @param sub_division:
        Sub-dividing the sinogram into subsections (along rotation angle axis).
    @param correction_range:
        Multiplicative correction factor is capped within given range.
    @param ncore:
        Number of cores to use for parallel processing.

    Returns
    -------
    @return:
        Radiograph stack with ring artifact removed.
    """
    # sanity check
    if arrays.ndim != 3:
        raise ValueError("This correction can only be used for a stack, i.e. a 3D image.")
    # NOTE:
    # additional work is needed to avoid duplicating arrays in memory
    ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
    with cf.ProcessPoolExecutor(max_workers=ncore) as executor:
        jobs = [
            executor.submit(
                remove_ring_artifact_Ketcham,
                arrays[:, sino_idx, :],
                kernel_size,
                sub_division,
                correction_range,
            )
            for sino_idx in range(arrays.shape[1])
        ]
    #
    sinos_corr = [job.result() for job in jobs]
    for i in range(arrays.shape[1]):
        arrays[:, i, :] = sinos_corr[i]
    return arrays


def remove_ring_artifact_Ketcham(
    sinogram: np.ndarray,
    kernel_size: int = 5,
    sub_division: int = 10,
    correction_range: tuple = (0.9, 1.1),
) -> np.ndarray:
    """
    Use the Ketcham method (doi:`10.1117/12.680939 <https://doi.org/10.1117/12.680939>`_) to remove ring artifact from given sinogram.

    Parameters
    ----------
    @param sinogram:
        Input sinogram.
    @param kernel_size:
        The size of the kernel (moving window) during local smoothing via median filter.
    @param sub_division:
        Sub-dividing the sinogram into subsections (along rotation angle axis).
    @param correction_range:
        Multiplicative correction factor is capped within given range.

    Returns
    -------
    @return:
        Sinogram with ring artifact removed.

    NOTE
    ----
        0. The ring artifact refers to the halo type artifacts present in the final reconstruction results, which is often caused by local detector/pixel gain error during measurement.
        1. This method can only be used on a single sinogram.
        2. This method is assuming the ring artifact is of multiplicative nature, i.e. measured = signal * error.
    """
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
