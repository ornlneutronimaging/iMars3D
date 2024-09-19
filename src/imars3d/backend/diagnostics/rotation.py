#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iMars3D: rotation center finding module."""
import logging
import numpy as np

import param
from imars3d.backend.util.functions import clamp_max_workers, calculate_chunksize
from multiprocessing.managers import SharedMemoryManager
from tqdm.contrib.concurrent import process_map
from tomopy.recon.rotation import find_center_pc
from imars3d.backend.diagnostics.tilt import find_180_deg_pairs_idx

logger = logging.getLogger(__name__)


class find_rotation_center(param.ParameterizedFunction):
    """
    Automatically find the rotation center from a given radiograph stack.

    Parameters
    ----------
    arrays: np.ndarray
        3D array of images, the first dimension is the rotation angle omega
    angles: np.ndarray
        array of angles in degrees or radians, which must match the order of arrays
    in_degrees: bool = True
        whether angles are in degrees or radians, default is True (degrees)
    atol_deg: Optional[float] = None
        tolerance for the search of 180 deg paris, default is None ("auto")
    num_pairs: int = 1
        Number of pairs to look for.
        Specifying -1 means as many pairs as possible.
        The pairs will be equally spaced if possible.
        If the number of pairs requested is more than half of what is available, it will take the first n-piars.
    max_workers: int = 0
        number of cores to use for parallel median filtering, default is 0, which means using all available cores.
    tqdm_class: panel.widgets.Tqdm
        Class to be used for rendering tqdm progress

    Returns
    -------
        rotation center in pixels
    """

    arrays = param.Array(doc="3D array of images, the first dimension is the rotation angle omega.", default=None)
    angles = param.Array(
        doc="array of angles in degrees or radians, which must match the order of arrays", default=None
    )
    in_degrees = param.Boolean(default=True, doc="whether angles are in degrees or radians, default is True (degrees)")
    atol_deg = param.Number(
        default=None,
        doc="tolerance for the search of 180 deg paris, default is None (auto)",
    )
    num_pairs = param.Integer(
        default=1, bounds=(-1, None), doc="Number of pairs to look for. Specifying -1 means as many pairs as possible."
    )
    max_workers = param.Integer(
        default=0,
        bounds=(0, None),
        doc="Maximum number of processes to use for parallel median filtering, default is 0, which means using all available cores.",
    )
    tqdm_class = param.ClassSelector(class_=object, doc="Progress bar to render with")

    def __call__(self, **params):
        """See class level documentation for help."""
        logger.info("Executing Filter: Find Rotation Center")
        _ = self.instance(**params)
        params = param.ParamOverrides(self, params)

        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = clamp_max_workers(params.max_workers)

        val = self._find_rotation_center(
            arrays=params.arrays,
            angles=params.angles,
            in_degrees=params.in_degrees,
            atol=params.atol_deg,
            num_pairs=params.num_pairs,
            max_workers=self.max_workers,
            tqdm_class=params.tqdm_class,
        )
        logger.info("FINISHED Executing Filter: Find Rotation Center")
        return val

    def _find_rotation_center(
        self,
        arrays: np.ndarray,
        angles: np.ndarray,
        in_degrees: bool = True,
        atol: float = None,
        num_pairs: int = 1,
        max_workers: int = -1,
        tqdm_class=None,
    ) -> float:
        # sanity check input
        if arrays.ndim != 3:
            msg = "arrays must be 3D (valid radiograph stack)"
            logger.error(msg)
            raise ValueError(msg)
        # locate 180 degree pairs
        idx_low, idx_hgh = find_180_deg_pairs_idx(angles, atol=atol, in_degrees=in_degrees)
        # decide how many pairs to use
        if num_pairs <= 0 or num_pairs >= idx_low.size:
            logger.info("Using all pairs of angles")
        elif num_pairs == 1:
            idx_low = [idx_low[0]]
            idx_hgh = [idx_hgh[0]]
            logger.info("Using one pair of angles")
        else:
            # integer division to get correct size if possible
            span = idx_low.size // num_pairs
            # get equally spaced items if possible
            if span > 1:
                idx_low = idx_low[::span]
                idx_hgh = idx_hgh[::span]
            # trim down to the requested number
            # the selected angels are not equally spaced
            if idx_low.size > num_pairs:
                idx_low = idx_low[:num_pairs]
                idx_hgh = idx_hgh[:num_pairs]
            logger.info(f"Using {idx_low.size} pairs of angles")

        # process
        max_workers = clamp_max_workers(max_workers)
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
            kwargs = {
                "max_workers": max_workers,
                "chunksize": calculate_chunksize(len(idx_low), max_workers),
                "desc": "Finding rotation center",
            }
            if tqdm_class:
                kwargs["tqdm_class"] = tqdm_class
            rst = process_map(
                find_center_pc, [shm_arrays[il] for il in idx_low], [shm_arrays[ih] for ih in idx_hgh], **kwargs
            )
        # use the median value
        return (np.median(rst),)
