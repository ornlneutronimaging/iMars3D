from functools import cache
import numpy as np
import pytest
import tomopy
from imars3d.backend.diagnostics.rotation import find_rotation_center

# all tests share a consistent set of omeaga angles
# these are in radians
OMEGAS = np.linspace(0, np.pi * 2, 181)

# decorator creates a dict of previous parameter/return pairs
# the cache does not empty
# each call takes ~1s
# Time difference on 2022-12-09 was 17s vs 11s


@cache
def get_synthetic_stack(
    center: float,
) -> np.ndarray:
    """
    Generate synthetic radiograph stack with given rotation center and rotation angles.

    Parameter
    ---------
    @param center:
        Rotation center

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
        OMEGAS,
        emission=False,
        center=center,
    )
    return projs


@pytest.mark.parametrize(
    "num_pairs",
    [-1, 0, 1, 44, 45, 46, 200],
)
def test_pairs(num_pairs):
    CENTER_REF = 80.5
    projs = get_synthetic_stack(CENTER_REF)

    center_calc = find_rotation_center(arrays=projs, angles=OMEGAS, in_degrees=False, num_pairs=num_pairs)
    # answer within the same pixel should be sufficient for most cases
    np.testing.assert_almost_equal(center_calc, CENTER_REF, decimal=1)


@pytest.mark.parametrize(
    "center_ref",
    [
        70,
        80.5,
        100.2,
        119.5,
    ],
)
def test_differrent_centers(center_ref):
    # NOTE: unit of omegas is handled by find_180_deg_pairs_idx
    projs = get_synthetic_stack(center_ref)
    # this is using default number of pairs (1)
    center_calc = find_rotation_center(arrays=projs, angles=OMEGAS, in_degrees=False)
    # verify
    # NOTE:
    # answer within the same pixel should be sufficient for most cases
    np.testing.assert_allclose(center_calc, center_ref, atol=0.2)


def test_wrong_dimension():
    projs = np.random.random(100).reshape(10, 10)
    with pytest.raises(ValueError):
        find_rotation_center(arrays=projs, angles=OMEGAS)


if __name__ == "__main__":
    pytest.main([__file__])
