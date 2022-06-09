#!/usr/bin/env python3
import numpy as np
import pytest
import skimage
import tomopy
from scipy.spatial.transform import Rotation as R
from imars3dv2.filters.tilt import calculate_tilt
from imars3dv2.filters.tilt import calculate_dissimilarity
from imars3dv2.filters.tilt import calculate_shift


def get_tilted_rot_axis(
    tilt_inplane: float,
    tilt_outplane: float,
) -> np.ndarray:
    """
    Get a unit vector as tilted rotation axis from in-plane tilt angle and out
    of plane tilt angle.

    Parameters
    ---------
    @param tilt_inplane:
        In-plane (xy) tilt angle in radians
    @param tilt_outplane:
        Out-of-plane (yz) tile angle in radians

    Returns
    -------
    @returns
        rotation axis as a unit vector

    NOTE
    ----
    The out-of-plane tilt is a feature intended for future tilt correction
    development.  The current tilt correction from iMars3D is restricted for
    in-plane tilt only.
    """
    # Use Beamline coordinate system where
    #   z: incident beam direction
    #   y: vertical direction, also parallel to the perfect rotation axis (assuming the camera is perfectly leveled
    #   x: follow the right-hand rule
    # so the imaging plane is x-y plane.
    # Therefore, if the tilted rotation axis is (xr, yr, zr), we have
    #  tan(alpha) = xr/yr
    #  tan(beta) = zr/yr
    # Let yr = 1, then the tilted rotation axis is (tan(alpha), 1, tan(beta)), then normalized to be a unit vector
    rot_vec = np.array([np.tan(tilt_inplane), 1.0, np.tan(tilt_outplane)])
    return rot_vec / np.linalg.norm(rot_vec)


def two_sphere_system(
    omega: float,
    rot_axis: np.ndarray,
    size: int = 200,
    s1_center_rel: np.ndarray = np.array([0.2, 0.2, 0.2]),
    s1_radius_rel: float = 0.05,
    s2_center_rel: np.ndarray = np.array([-0.2, -0.2, -0.2]),
    s2_radius_rel: float = 0.06,
) -> np.ndarray:
    """
    Two-sphere system rotated around given rotatino axis by given rotation angle as a 3D numpy array.

    Parameter
    ---------
    @param omega:
        Rotation angle in radians
    @param rot_axis:
        Unit vector representing the rotation axis
    @param size:
        The dimension of the 3D numpy array encapsulating the two sphere system
    @param s1_center_rel:
        The initial relative position vector (w.r.t center of the 3D volume) for the center of sphere 1
    @param s1_radius_rel:
        The radius (in relative unit) of sphere 1
    @param s2_center_rel:
        The initial relative position vector (w.r.t center of the 3D volume) for the center of sphere 2
    @param s2_radius_rel:
        The radius (in relative unit) of sphere 2

    Returns
    -------
    @returns
        A 3D numpy array depicting the two-sphere system, where air is 0, and object is 1.
    """
    # get the rotation object
    rot_axis = rot_axis / np.linalg.norm(rot_axis)
    rotation = R.from_rotvec(-omega * rot_axis)
    # calculate the rotated sphere centers
    # sphere 1
    s1_rel = rotation.apply(s1_center_rel)
    # sphere 2
    s2_rel = rotation.apply(s2_center_rel)
    # get the index grid
    # NOTE: extend the range to make sure the sphere is not rotated out of the volume
    # grid_x, grid_y, grid_z = np.mgrid[0:size, 0:size, 0:size]
    # remapping to compensate for the strange coordinate system in tomopy projector
    grid_y, grid_z, grid_x = np.mgrid[0:size, 0:size, 0:size]
    # rescale to [-0.5, 0.5]
    grid_x = grid_x / (size - 1) - 0.5
    grid_y = -(grid_y / (size - 1) - 0.5)
    grid_z = grid_z / (size - 1) - 0.5
    # init volume
    vol = np.zeros_like(grid_x)
    # mark the voxels of sphere 1 to be 1
    s1_dist_squared = (grid_x - s1_rel[0]) ** 2 + (grid_y - s1_rel[1]) ** 2 + (grid_z - s1_rel[2]) ** 2
    r1_squared = s1_radius_rel ** 2
    vol[s1_dist_squared < r1_squared] = 1.0
    # mark the voxels of sphere 2 to be 2
    s2_dist_squared = (grid_x - s2_rel[0]) ** 2 + (grid_y - s2_rel[1]) ** 2 + (grid_z - s2_rel[2]) ** 2
    r2_squared = s2_radius_rel ** 2
    vol[s2_dist_squared < r2_squared] = 1.0
    return vol


def virtual_cam(sample: np.ndarray, dynamic_range: int = 50_000) -> np.ndarray:
    """
    Projecting the 3D volume (sample) on to the x-z plane.

    Parameter
    ---------
    @param sample:
        3D numpy array representing the volume where air is 0 and object is 1
    @param dynamic_range:
        The dynamic range of the output image.

    Returns
    -------
    @returns
        2D numpy array representing the projected volume
    """
    img = sample.sum(axis=1)
    img = (img.max() - img) / (img.max() - img.min())
    return img * dynamic_range


@pytest.mark.parametrize(
    "tilt_reference",
    [
        0.0,
        0.05,
        0.1,
        1.0,
    ],
)
def test_calculate_tilt(tilt_reference):
    """
    Test the tilt correction with no tilt.
    """
    tilt_rad = np.degrees(tilt_reference)
    # get the rotation axis
    # NOTE:
    # we need to tilt the image -tilt in order to get the tilt angle as + value.
    rot_aixs_tilted = get_tilted_rot_axis(tilt_inplane=-tilt_rad, tilt_outplane=0.0)
    # radiograph at 0 deg
    img0 = virtual_cam(two_sphere_system(0, rot_aixs_tilted, size=100))
    # radiograph at 180 deg
    img180 = virtual_cam(two_sphere_system(np.pi, rot_aixs_tilted, size=100))
    # calculate the tilt angle
    tilt_angle = calculate_tilt(img0, img180)
    # verify
    assert np.isclose(tilt_angle, 0.0)


def test_calculate_dissimilarity():
    # use stock image to speed up testing
    img0 = skimage.data.brain()[2, :, :]
    img180 = np.fliplr(img0)
    # case 1: perfectly matched 180 deg pair
    err = calculate_dissimilarity(0, img0, img180)
    assert np.isclose(err, 0.0)
    # case 2: moving away from minimum increases error
    err_1 = calculate_dissimilarity(1, img0, img180)
    err_2 = calculate_dissimilarity(2, img0, img180)
    assert err_1 > err_2


def test_calculate_shift():
    # use tomopy to generate images with different rotation center
    shepp3d = tomopy.misc.phantom.shepp3d()
    # case 0: centered rotation axis -> no shift
    projs = tomopy.sim.project.project(
        shepp3d,
        np.array([0, np.pi]),
        emission=False,
    )
    shift_calculated = calculate_shift(projs[0], projs[1])
    assert np.isclose(shift_calculated, 0.0)
    # case 1: positive shift
    projs = tomopy.sim.project.project(
        shepp3d,
        np.array([0, np.pi]),
        emission=False,
        center=100,
    )
    assert np.isclose(shift_calculated, 16.0)
    # case 2: negative shift
    projs = tomopy.sim.project.project(
        shepp3d,
        np.array([0, np.pi]),
        emission=False,
        center=50,
    )
    shift_calculated = calculate_shift(projs[0], projs[1])
    assert np.isclose(shift_calculated, -84.0)


if __name__ == "__main__":
    pytest.main([__file__])