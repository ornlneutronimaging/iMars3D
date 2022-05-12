#!/usr/bin/env python3
import numpy as np
import pytest
from imars3dv2.filters.crop import crop, detect_bounds


def generate_fake_proj(
    img_shape: tuple,
    slit_pos: tuple,
    intensity_outter_low: int = 910,
    intensity_outter_high: int = 930,
    intensity_inner_low: int = 15_000,
    intensity_inner_high: int = 35_080,
):
    """
    Generate a fake projection image.
    """
    # generate background
    proj = np.random.randint(
        low=intensity_outter_low,
        high=intensity_outter_high,
        size=img_shape,
        dtype=np.uint16,
    )
    # unpack slit positions
    left, right, top, bottom = slit_pos
    # generate FOV
    fov = np.random.randint(
        low=intensity_inner_low,
        high=intensity_inner_high,
        size=(bottom - top + 1, right - left + 1),
        dtype=np.uint16,
    )
    # add FOV to background
    proj[top : bottom + 1, left : right + 1] = fov
    return proj


def test_crop_manual():
    """
    Check the manual crop produce the correct numpy shape.
    """
    n_imgs = 3
    img_shape = (512, 1024)
    slit_pos = (400, 824, 100, 412)  # left, right, top, bottom
    imgstack = np.array([generate_fake_proj(img_shape, slit_pos) for _ in range(n_imgs)])
    # manual crop
    imgstack_cropped = crop(imgstack, slit_pos)
    assert imgstack_cropped.shape == (n_imgs, 312, 424)
    # auto crop
    imgstack_cropped = crop(imgstack)
    assert imgstack_cropped.shape == (n_imgs, 312, 424)


def test_auto_detect_slit_position():
    """
    check the case where slits are present, i.e I_inner > I_outer
    """
    img_shape = (512, 1024)
    slit_pos = (400, 824, 100, 412)  # left, right, top, bottom
    img = generate_fake_proj(img_shape, slit_pos)
    # auto crop
    slit_pos_detected = detect_bounds(img)
    np.testing.assert_allclose(
        np.array(slit_pos_detected),
        np.array(slit_pos),
        atol=1,  # bounds off by 1 pixel is still acceptable
    )


def test_auto_detect_object_in_fov():
    """
    check the auto detection for an object with in the FOV without slits, i.e.
    inner < outter
    """
    img_shape = (512, 1024)
    slit_pos = (400, 824, 100, 412)  # left, right, top, bottom
    img = generate_fake_proj(
        img_shape,
        slit_pos,
        intensity_outter_low=30_000,
        intensity_outter_high=31_000,
        intensity_inner_low=10_000,
        intensity_inner_high=15_000,
    )
    # auto detect
    slit_pos_detected = detect_bounds(img, expand_ratio=0)
    np.testing.assert_allclose(
        np.array(slit_pos_detected),
        np.array(slit_pos),
        atol=1,  # bounds off by 1 pixel is still acceptable
    )


def test_crop_wrong_array_dim():
    arrays = np.array([1, 2, 3])
    with pytest.raises(ValueError):
        crop(arrays)


def test_auto_detect_wrong_array_dim():
    arrays = np.array([1, 2, 3])
    with pytest.raises(ValueError):
        detect_bounds(arrays)


def test_auto_detect_no_signal():
    img_shape = (512, 1024)
    slit_pos = (400, 824, 100, 412)  # left, right, top, bottom
    img = generate_fake_proj(
        img_shape,
        slit_pos,
        intensity_outter_low=10_000,
        intensity_outter_high=11_000,
        intensity_inner_low=10_000,
        intensity_inner_high=11_000,
    )
    slit_pos_detected = detect_bounds(img, expand_ratio=0)
    # since there is no signal, the detector will just return the whole image
    # range.
    np.testing.assert_allclose(
        np.array(slit_pos_detected),
        np.array([0, 1023, 0, 511]),
        atol=1,  # bounds off by 1 pixel is still acceptable
    )


if __name__ == "__main__":
    pytest.main("__file__")
