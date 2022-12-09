#!/usr/bin/env python3
import numpy as np
import pytest
import skimage
import tomopy
from scipy.spatial.transform import Rotation as R
from skimage.transform import rotate
from imars3d.backend.diagnostics.tilt import calculate_tilt
from imars3d.backend.diagnostics.tilt import calculate_dissimilarity
from imars3d.backend.diagnostics.tilt import calculate_shift
from imars3d.backend.diagnostics.tilt import find_180_deg_pairs_idx
from imars3d.backend.diagnostics.tilt import apply_tilt_correction
from imars3d.backend.diagnostics.tilt import tilt_correction
from imars3d.ui.widgets import Tqdm


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
    Two-sphere system rotated around given rotation axis by given rotation angle as a 3D numpy array.

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
    r1_squared = s1_radius_rel**2
    vol[s1_dist_squared < r1_squared] = 1.0
    # mark the voxels of sphere 2 to be 2
    s2_dist_squared = (grid_x - s2_rel[0]) ** 2 + (grid_y - s2_rel[1]) ** 2 + (grid_z - s2_rel[2]) ** 2
    r2_squared = s2_radius_rel**2
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
    tilt_rad = np.radians(tilt_reference)
    # get the rotation axis
    # NOTE:
    # we need to tilt the image -tilt in order to get the tilt angle as + value.
    rot_aixs_tilted = get_tilted_rot_axis(tilt_inplane=-tilt_rad, tilt_outplane=0.0)
    # radiograph at 0 deg
    img0 = virtual_cam(two_sphere_system(0, rot_aixs_tilted, size=200))
    # radiograph at 180 deg
    img180 = virtual_cam(two_sphere_system(np.pi, rot_aixs_tilted, size=200))
    # calculate the tilt angle
    tilt_angle = calculate_tilt(img0, img180).x
    # verify
    # NOTE: tolerance is set to half a pixel at the edge of the FOV
    np.testing.assert_allclose(tilt_angle, tilt_reference, atol=np.degrees(0.5 / 100))


def test_calculate_dissimilarity():
    # use stock image to speed up testing
    img0 = skimage.data.brain()[2, :, :]
    img180 = np.fliplr(img0)
    # case 1: perfectly matched 180 deg pair
    err = calculate_dissimilarity(0, img0, img180)
    np.testing.assert_allclose(err, 0.0)
    # case 2: moving away from minimum increases error
    err_1 = calculate_dissimilarity(1, img0, img180)
    err_2 = calculate_dissimilarity(2, img0, img180)
    assert err_1 < err_2
    err_3 = calculate_dissimilarity(1, img180, img0)
    err_4 = calculate_dissimilarity(2, img180, img0)
    assert err_3 < err_4
    # case 3: ensure dissimilarity calculate is abelian
    err_ab = calculate_dissimilarity(1, img0, img180)
    err_ba = calculate_dissimilarity(-1, img180, img0)
    np.testing.assert_allclose(err_ab, err_ba, atol=1e-4)


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
    np.testing.assert_allclose(shift_calculated, 0.0)
    # case 1: positive shift
    projs = tomopy.sim.project.project(
        shepp3d,
        np.array([0, np.pi]),
        emission=False,
        center=100,
    )
    shift_calculated = calculate_shift(projs[0], projs[1])
    np.testing.assert_allclose(shift_calculated, 16.0)
    # case 2: negative shift
    projs = tomopy.sim.project.project(
        shepp3d,
        np.array([0, np.pi]),
        emission=False,
        center=50,
    )
    shift_calculated = calculate_shift(projs[0], projs[1])
    np.testing.assert_allclose(shift_calculated, -84.0)


def test_find_180_deg_pairs():
    # prepare the input list of angles in radians
    omegas = np.random.random(5) * np.pi
    omegas = np.array(list(omegas) + list(omegas + np.pi))
    # get the pairs
    low_range_idx, high_range_idx = find_180_deg_pairs_idx(omegas, in_degrees=False)
    # verify
    np.testing.assert_equal(low_range_idx, np.array([0, 1, 2, 3, 4]))
    np.testing.assert_equal(high_range_idx, np.array([5, 6, 7, 8, 9]))
    # test explicit atol
    omegas = np.sort(omegas)
    atol = np.min(np.diff(omegas)) / 2.0
    low_range_idx, high_range_idx = find_180_deg_pairs_idx(omegas, in_degrees=False, atol=atol)
    np.testing.assert_equal(low_range_idx, np.array([0, 1, 2, 3, 4]))
    np.testing.assert_equal(high_range_idx, np.array([5, 6, 7, 8, 9]))
    # test incorrect input
    omegas = np.random.random(5 * 5) * np.pi
    omegas = omegas.reshape(5, 5)
    with pytest.raises(ValueError):
        low_range_idx, high_range_idx = find_180_deg_pairs_idx(omegas)


def test_apply_tilt_correction():
    # case 1: 2d image
    # use stock image to speed up testing
    img_ref = skimage.data.brain()[2, :, :]
    tilt = 1.0  # deg
    img_tilted = rotate(img_ref, tilt, resize=False)
    img_corrected = apply_tilt_correction(arrays=img_tilted, tilt=tilt)
    # verify
    # NOTE: the rotate will alter the value due to interpolation, so it is not
    #       possible to compare the exact values.
    err_tilted = np.linalg.norm(img_tilted - img_ref) / img_ref.size
    err_corrected = np.linalg.norm(img_corrected - img_ref) / img_ref.size
    assert err_tilted > err_corrected
    # case 1a: 2d image with progress bar
    # use stock image to speed up testing
    img_ref = skimage.data.brain()[2, :, :]
    tilt = 1.0  # deg
    img_tilted = rotate(img_ref, tilt, resize=False)
    img_corrected = apply_tilt_correction(arrays=img_tilted, tilt=tilt, tqdm_class=Tqdm())
    # verify
    # NOTE: the rotate will alter the value due to interpolation, so it is not
    #       possible to compare the exact values.
    err_tilted = np.linalg.norm(img_tilted - img_ref) / img_ref.size
    err_corrected = np.linalg.norm(img_corrected - img_ref) / img_ref.size
    assert err_tilted > err_corrected
    # case 2: 3d image stack
    imgs_ref = skimage.data.brain()[:3, :, :]
    tilt = 1.0  # deg
    imgs_tilted = np.array([rotate(img, tilt, resize=False) for img in imgs_ref])
    imgs_corrected = apply_tilt_correction(arrays=imgs_tilted, tilt=tilt)
    # verify
    # NOTE: similar as the 2d case
    err_tilted = np.linalg.norm(imgs_tilted - imgs_ref) / img_ref.size
    err_corrected = np.linalg.norm(imgs_corrected - imgs_ref) / img_ref.size
    assert err_tilted > err_corrected
    # case 3: incorrect input
    with pytest.raises(ValueError):
        imgs_incorrect = np.arange(10)
        apply_tilt_correction(arrays=imgs_incorrect, tilt=tilt)


def test_tilt_correction():
    # error_0: incorrect dimension
    with pytest.raises(ValueError):
        tilt_correction(arrays=np.arange(10), tilt=1.0)
    # make synthetic data
    size = 100
    rot_axis_ideal = get_tilted_rot_axis(0, 0)
    omegas = np.linspace(0, np.pi * 2, 11)
    projs_ref = np.array([virtual_cam(two_sphere_system(omega, rot_axis_ideal, size=size)) for omega in omegas])
    # case 1: null
    projs_corrected = tilt_correction(arrays=projs_ref, rot_angles=omegas)
    # verify
    np.testing.assert_allclose(projs_corrected, projs_ref)
    # case 1a: null with the progress bar
    projs_corrected = tilt_correction(arrays=projs_ref, rot_angles=omegas, tqdm_class=Tqdm())
    np.testing.assert_allclose(projs_corrected, projs_ref)
    # case 2: small angle tilt
    tilt_inplane = np.radians(0.5)
    tilt_outplane = np.radians(0.0)
    rot_axis = get_tilted_rot_axis(-tilt_inplane, tilt_outplane)
    projs_tilted = np.array([virtual_cam(two_sphere_system(omega, rot_axis, size=size)) for omega in omegas])
    projs_corrected = tilt_correction(arrays=projs_tilted, rot_angles=omegas)
    # verify
    # the corrected one should close to the ideal (non-tilted) one
    diff_corrected = projs_corrected / projs_corrected.max() - projs_ref / projs_ref.max()
    err_corrected = np.linalg.norm(diff_corrected) / projs_ref.size
    assert err_corrected < 1e-3
    # case 3: large angle tilt
    tilt_inplane = np.radians(3.0)
    tilt_outplane = np.radians(0.0)
    rot_axis = get_tilted_rot_axis(-tilt_inplane, tilt_outplane)
    projs_tilted = np.array([virtual_cam(two_sphere_system(omega, rot_axis, size=size)) for omega in omegas])
    projs_corrected = tilt_correction(arrays=projs_tilted, rot_angles=omegas, cut_off_angle_deg=0.1)
    # verify
    # the corrected one should close to the ideal (non-tilted) one
    diff_corrected = projs_corrected / projs_corrected.max() - projs_ref / projs_ref.max()
    err_corrected = np.linalg.norm(diff_corrected) / projs_ref.size
    assert err_corrected < 1e-3


if __name__ == "__main__":
    pytest.main([__file__])
