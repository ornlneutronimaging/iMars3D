#!/usr/bin/env python3
import numpy as np
import pytest
import tomopy
from imars3d.backend.reconstruction import recon


def test_recon():
    # generate testing data for reconstruction
    omegas = np.linspace(0, np.pi * 2, 181)
    shepp3d = tomopy.misc.phantom.shepp3d(size=129)
    projs = tomopy.sim.project.project(shepp3d, omegas, emission=True)

    with pytest.raises(ValueError):
        # check that input is 3-dimensional
        recon(projs[0, :, :], omegas)

    # run reconstruction
    result = recon(projs, omegas)

    # extract a region around the center of each slice to compare
    center = int(result[64].shape[1] / 2)
    result_slice = result[64, center - 30 : center + 30, center - 30 : center + 30]

    center = int(shepp3d[64].shape[1] / 2)
    shepp_slice = shepp3d[64, center - 30 : center + 30, center - 30 : center + 30]

    # reconstructed image should roughly match original
    assert np.linalg.norm(result_slice - shepp_slice) / result_slice.size < 1e-3


if __name__ == "__main__":
    pytest.main([__file__])
