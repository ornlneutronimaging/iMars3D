#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iMars3D: rotation center finding module."""
import numpy as np
import param
import multiprocessing
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
import tomopy.util.mproc as mproc
from tomopy.recon.rotation import find_center_pc
from imars3d.backend.diagnostics.tilt import find_180_deg_pairs_idx

logger = param.get_logger(__name__)
logger.name = __name__


class find_rotation_center(param.ParameterizedFunction):
    """
    Automatically find the rotation center from a given radiograph stack.

    Parameters
    ----------
    arrays: 3D array of images, the first dimension is the rotation angle omega
    angles: array of angles in degrees or radians, which must match the order of arrays
    in_degrees: whether angles are in degrees or radians, default is True (degrees)
    atol_deg: tolerance for the search of 180 deg paris, default is 0.1 degrees
    max_workers: number of cores to use for parallel median filtering, default is 0, which means using all available cores.

    Returns
    -------
        rotation center in pixels
    """

    arrays = param.Array(doc="3D array of images, the first dimension is the rotation angle omega.")
    angles = param.Array(doc="array of angles in degrees or radians, which must match the order of arrays")
    in_degrees = param.Boolean(default=True, doc="whether angles are in degrees or radians, default is True (degrees)")
    atol_deg = param.Number(
        default=1e-3,
        doc="tolerance for the search of 180 deg paris, default is 0.1 degrees",
    )
    max_workers = param.Integer(
        default=0,
        bounds=(0, max(1, multiprocessing.cpu_count() - 2)),
        doc="Maximum number of processes to use for parallel median filtering, default is -1, which means using all available cores.",
    )

    def __call__(self, **params):
        logger.info(f"Executing Filter: Find Rotation Center")
        _ = self.instance(**params)
        params = param.ParamOverrides(self, params)
        val = self._find_rotation_center(
            params.arrays, params.angles, params.in_degrees, params.atol_deg, params.max_workers
        )
        logger.info(f"FINISHED Executing Filter: Find Rotation Center")
        return val

    def _find_rotation_center(
        self,
        arrays: np.ndarray,
        angles: np.ndarray,
        in_degrees: bool = True,
        atol_deg: float = 1e-3,
        max_workers: int = -1,
    ) -> float:
        # sanity check input
        if arrays.ndim != 3:
            msg = "arrays must be 3D (valid radiograph stack)"
            logger.error(msg)
            raise ValueError(msg)
        # locate 180 degree pairs
        atol = atol_deg if in_degrees else np.radians(atol_deg)
        idx_low, idx_hgh = find_180_deg_pairs_idx(angles, atol=atol, in_degrees=in_degrees)
        # process
        max_workers = max(1, multiprocessing.cpu_count() - 2) if max_workers <= 0 else max_workers
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
                max_workers=max_workers,
                desc="Finding rotation center",
            )
        # use the median value
        return np.median(rst)
