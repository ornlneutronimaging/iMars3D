#!/usr/bin/env python3
"""reconstruction module for imars3d package."""
import logging
import numpy as np
import param
from tomopy.recon.algorithm import recon as tomo_recon

logger = logging.getLogger(__name__)


class recon(param.ParameterizedFunction):
    """
    Perform reconstruction on a stack of tomographic data.

    Parameters
    ----------
    arrays: np.ndarray
        Input stack of tomography data
    theta: np.array
        Projection angles (in radians)
    center: float
        Rotation center
    algorithm: str
        Name of reconstruction algorithm
    filter_name: str
        Name of filter used for reconstruction

    Return
    ------
    np.ndarray
        Reconstructed tomographic data
    """

    arrays = param.Array(
        doc="Input stack of tomography data",
    )
    theta = param.Array(
        doc="Projection angles (in radians)",
    )
    center = param.Number(
        default=None,
        doc="Rotation center",
    )
    algorithm = param.String(
        default="gridrec",
        doc="Name of reconstruction algorithm",
    )
    filter_name = param.String(
        default="hann",
        doc="Name of filter used for reconstruction",
    )

    def __call__(self, **params):
        logger.info("Executing Filter: Reconstruction")
        # forced type+bounds check
        _ = self.instance(**params)
        # sanitize args
        params = param.ParamOverrides(self, params, allow_extra_keywords=True)
        reconstructed_image = self._recon(
            params.arrays,
            params.theta,
            params.center,
            params.algorithm,
            params.filter_name,
            **params.extra_keywords(),
        )

        logger.info(f"FINISHED Executing Filter: Reconstruction: {params.filter_name}")
        return reconstructed_image

    def _recon(self, arrays, theta, center, algorithm, filter_name, **kwargs) -> np.ndarray:

        if arrays.ndim != 3:
            raise ValueError("Expected input array to have 3 dimensions")

        # TODO: allow different backends besides tomopy
        result = tomo_recon(arrays, theta, center=center, algorithm=algorithm, filter_name=filter_name, **kwargs)
        return result
