#!/usr/bin/env python3
import numpy as np
from tomopy.recon.algorithm import recon as tomo_recon


def recon(
    sinogram: np.ndarray,
    theta: np.array,
    center: np.array = None,
    algorithm: str = "gridrec",
    filter_name: str = "hann",
    **kwargs
) -> np.ndarray:
    """
    Perform reconstruction on a stack of sinograms

    Parameters
    ----------
    @param sinogram:
        Input stack of sinograms
    @param theta:
        Projection angles (in radians)
    @param center:
        Rotation center
    @param algorithm:
        Name of reconstruction algorithm
    @param filter_name:
        Name of filter used for reconstruction

    Return
    ------
    @return
        Reconstructed sinograms
    """

    if sinogram.ndim != 3:
        raise ValueError("Expected input sinogram array to have 3 dimensions")

    # TODO: allow different backends besides tomopy
    result = tomo_recon(sinogram, theta, center=center, algorithm=algorithm, filter_name=filter_name, **kwargs)
    return result
