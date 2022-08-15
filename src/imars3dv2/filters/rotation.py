#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import tomopy
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
import tomopy.util.mproc as mproc
from tomopy.recon.rotation import find_center_pc
from imars3dv2.filters import find_180_deg_pairs_idx


def find_rotation_center(
    arrays: np.ndarray,
    angles: np.ndarray,
    in_degrees: bool = True,
    atol_deg: float = 1e-3,
    ncore: int = -1,
) -> float:
    """
    Automatically find the rotation center from a given radiograph stack.

    Parameters
    ----------
    @param arrays: 3D array of images, the first dimension is the rotation angle omega
    @param angles: array of angles in degrees or radians, which must match the order of arrays
    @param in_degrees: whether angles are in degrees or radians, default is True (degrees)
    @param atol_deg: tolerance for the search of 180 deg paris, default is 0.1 degrees
    @param ncore: number of cores to use for parallel median filtering, default is -1, which means using all available cores.

    Returns
    -------
    @return: rotation center in pixels
    """
    # sanity check input
    if arrays.ndim != 3:
        raise ValueError("arrays must be 3D (valid radiograph stack)")
    # locate 180 degree pairs
    atol = atol_deg if in_degrees else np.radians(atol_deg)
    idx_low, idx_hgh = find_180_deg_pairs_idx(angles, atol=atol, in_degrees=in_degrees)
    # process
    ncore = mproc.mp.cpu_count() if ncore == -1 else int(ncore)
    # use shared memory model and tqdm wrapper for multiprocessing to reduce
    # runtime memory footprint
    with SharedMemoryManager() as smm:
        # create the shared memory
        shm = smm.SharedMemory(arrays.nbytes)
        # create a numpy array point to the shared memory
        shm_arrays = np.ndarray(
            arrays.shape,
            dtype=arrays.dtype,
            buffer=shm.buf,
        )
        # copy data
        np.copyto(shm_arrays, arrays)
        # map the multiprocessing calls
        rst = process_map(
            find_center_pc,
            [shm_arrays[il] for il in idx_low],
            [shm_arrays[ih] for ih in idx_hgh],
            max_workers=ncore,
            desc="Finding rotation center",
        )
    # use the median value
    return np.median(rst)
