#!/usr/bin/env python3
import numpy as np
import pytest
import tomopy
from imars3d.backend.diagnostics.rotation import find_rotation_center


def get_synthetic_stack(
    center: float,
    omegas: np.ndarray,
) -> np.ndarray:
    """
    Generate synthetic radiograph stack with given rotation center and rotation angles.

    Parameter
    ---------
    @param center:
        Rotation center
    @param omegas:
        Rotation angles in radians

    Return
    ------
    @return
        Radiograph stack of synthetic shepp3d rotating around center at omegas locations.
    """
    # NOTE:
    # the simulator has some rounding errors, and we need to push the input center by half
    # a pixel to avoid the rounding error
    center = center + 0.5 if center else center
    shepp3d = tomopy.misc.phantom.shepp3d(size=129)
    projs = tomopy.sim.project.project(
        shepp3d,
        omegas,
        emission=False,
        center=center,
    )
    return projs


@pytest.mark.parametrize(
    "center_ref",
    [
        70,
        80.5,
        100.2,
        119.5,
    ],
)
def test_find_rotation_center(center_ref):
    #
    # case 0: valid input
    # NOTE: unit of omegas is handled by find_180_deg_pairs_idx
    omegas = np.linspace(0, np.pi * 2, 181)
    projs = get_synthetic_stack(center_ref, omegas)
    center_calc = find_rotation_center(projs, omegas, in_degrees=False)
    # verify
    # NOTE:
    # answer within the same pixel should be sufficient for most cases
    np.testing.assert_almost_equal(center_calc, center_ref, decimal=1)
    #
    # case 1: wrong dimension
    projs = np.random.random(100).reshape(10, 10)
    with pytest.raises(ValueError):
        find_rotation_center(projs, omegas)


if __name__ == "__main__":
    pytest.main([__file__])
