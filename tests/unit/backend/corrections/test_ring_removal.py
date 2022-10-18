#!/usr/bin/env python3
import numpy as np
import pytest
import tomopy
from imars3d.backend.corrections.ring_removal import remove_ring_artifact
from imars3d.backend.corrections.ring_removal import remove_ring_artifact_Ketcham


def get_synthetic_stack(N_omega: int = 181) -> np.ndarray:
    omegas = np.linspace(0, np.pi * 2, N_omega)
    shepp3d = tomopy.misc.phantom.shepp3d(size=200)
    # use emission type radiograph to skip the -log step
    projs = tomopy.sim.project.project(shepp3d, omegas, emission=True)
    return projs


def test_remove_ring_artifact():
    # get synthetic stack
    tomo_stack = get_synthetic_stack()
    # case 0: incorrect input
    with pytest.raises(ValueError):
        remove_ring_artifact(arrays=tomo_stack[0, :, :])
    # case 1: with added ring artifact
    # randomly adding 4 rings to each sinogram
    tomo_with_ring = np.array(tomo_stack)
    for i in range(tomo_with_ring.shape[1]):
        cols = np.random.randint(80, 200, 4)
        tomo_with_ring[:, i, cols[0]] *= 1.07
        tomo_with_ring[:, i, cols[1]] *= 1.05
        tomo_with_ring[:, i, cols[2]] *= 0.92
        tomo_with_ring[:, i, cols[3]] *= 0.90
    err_no_corr = np.linalg.norm(tomo_with_ring - tomo_stack)
    # perform correction
    tomo_corr = remove_ring_artifact(arrays=tomo_with_ring)
    err_corr = np.linalg.norm(tomo_corr - tomo_stack)
    # verify
    assert err_corr < err_no_corr


def test_remove_ring_artifact_Ketcham():
    # get synthetic stack
    tomo_stack = get_synthetic_stack()
    # case 0: incorrect input
    with pytest.raises(ValueError):
        remove_ring_artifact_Ketcham(sinogram=tomo_stack)
    # case 1: with ring artifact
    tomo_with_ring = np.array(tomo_stack)
    tomo_with_ring[:, 100, 80] *= 1.07
    tomo_with_ring[:, 100, 100] *= 1.05
    tomo_with_ring[:, 100, 150] *= 0.92
    tomo_with_ring[:, 100, 200] *= 0.92
    # select one sinogram for testing
    sino_ref = tomo_stack[:, 100, :]
    sino = tomo_with_ring[:, 100, :]
    sino_corrected = remove_ring_artifact_Ketcham(sinogram=sino, kernel_size=5)
    # verify
    #   The correction won't be perfect, but it should be better than the
    #   non-corrected one.
    err_no_correction = np.linalg.norm(sino - sino_ref) / sino.size
    err_correction = np.linalg.norm(sino_corrected - sino_ref) / sino.size
    assert err_correction < err_no_correction


if __name__ == "__main__":
    pytest.main([__file__])
