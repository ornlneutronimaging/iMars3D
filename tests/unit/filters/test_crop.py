#!/usr/bin/env python3
import numpy as np
import pytest
from imars3dv2.filters.crop import crop, detect_slit_positions


def generate_fake_proj(
    img_shape: tuple,
    slit_pos: tuple,
    intensity_bg_low: int = 910,
    intensity_bg_high: int = 930,
    intensity_fov_low: int = 15_000,
    intensity_fov_high: int = 35_080,
):
    """
    Generate a fake projection image.
    """
    # generate background
    proj = np.random.randint(
        low=intensity_bg_low,
        high=intensity_bg_high,
        size=img_shape,
        dtype=np.uint16,
    )
    # unpack slit positions
    left, right, top, bottom = slit_pos
    # generate FOV
    fov = np.random.randint(
        low=intensity_fov_low,
        high=intensity_fov_high,
        size=(top - bottom, right - left),
        dtype=np.uint16,
    )
    # add FOV to background
    proj[bottom:top, left:right] = fov
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


def test_auto_slit_pos_detection():
    """
    Check the auto slit position detection.
    """
    img_shape = (512, 1024)
    slit_pos = (400, 824, 100, 412)  # left, right, top, bottom
    img = generate_fake_proj(img_shape, slit_pos)
    # auto crop
    slit_pos_detected = detect_slit_positions(img)
    assert slit_pos_detected == slit_pos


def test_crop_auto_rectangular_object():
    """
    Check the auto slit position detection with a rectangular object in FOV.
    """
    img_shape = (512, 1024)
    slit_pos = (400, 824, 100, 412)  # left, right, top, bottom
    img = generate_fake_proj(img_shape, slit_pos)
    # add rectangular object
    img[200:300, 450:600] = np.iinfo(img.dtype).max - 100
    # auto crop
    slit_pos_detected = detect_slit_positions(img)
    assert slit_pos_detected == slit_pos


if __name__ == "__main__":
    pytest.main("( __file__")
