#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy
import concurrent.futures as cf
import tomopy.util.mproc as mproc
from tomopy.recon.rotation import find_center_pc
from imars3dv2.filters import find_180_deg_pairs_idx


def find_rotation_center(
    arrays: np.ndarray,
    angles: np.ndarray,
    in_degrees: bool = True,
    ncore: int = -1,
) -> float:
    """
    Automatically find the rotation center from a given radiograph stack.

    Parameters
    ----------
    @param arrays: 3D array of images, the first dimension is the rotation angle omega
    @param angles: array of angles in degrees or radians, which must match the order of arrays
    @param in_degrees: whether angles are in degrees or radians, default is True (degrees)
    @param ncore: number of cores to use for parallel median filtering, default is -1, which means using all available cores.

    Returns
    -------
    @return: rotation center in pixels
    """
    # sanity check input
    if arrays.ndim != 3:
        raise ValueError("arrays must be 3D (valid radiograph stack)")
    # locate 180 degree pairs
    idx_low, idx_hgh = find_180_deg_pairs_idx(angles, in_degrees=in_degrees)
    # process
    ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
    with cf.ProcessPoolExecutor(ncore) as e:
        # NOTE:
        # we are using the default half pixel tolerance for find_center_pc
        jobs = [
            e.submit(
                find_center_pc,
                arrays[il],
                arrays[lh],
            )
            for il, lh in zip(idx_low, idx_hgh)
        ]
    centers = np.array([job.result() for job in jobs])
    return np.median(centers)
