#!/usr/bin/env python3
import numpy as np
import pytest
import skimage
from scipy.ndimage import gaussian_filter
from imars3dv2.filters.normalization import normalization


def generate_fake_darkfield(
    img: np.ndarray,  # reference image
    bad_pixels: list = [],  # list of bad pixels
    bg_low: int = 910,  # background intensity lower bound (counts)
    bg_high: int = 930,  # background intensity upper bound (counts)
    noise_low: int = 1000,  # noise intensity lower bound (counts)
    noise_high: int = 1280,  # noise intensity upper bound (counts)
    noise_num_low: int = 20,  # number of noise pixels lower bound (counts)
    noise_num_high: int = 50,  # number of noise pixels upper bound (counts)
):
    n_row, n_col = img.shape
    dark = np.random.randint(
        low=bg_low,
        high=bg_high,
        size=(n_row, n_col),
        dtype=img.dtype,
    )
    for ix, iy in bad_pixels:
        dark[ix, iy] += np.random.randint(noise_low, noise_high)
    # make random noise
    noise_loc = np.random.randint(
        low=0,
        high=n_row,
        size=(np.random.randint(noise_num_low, noise_num_high), 2),
    )
    for ix, iy in noise_loc:
        dark[ix, iy] += np.random.randint(noise_low, noise_high)
    return dark


def generate_fake_whitefield(
    img: np.ndarray,  # reference image
    beam_low: int = 15_000,  # incident beam intensity lower bound (counts)
    beam_high: int = 35_000,  # incident beam intensity upper bound (counts)
    beam_height: int = 30,  # incident beam height in pixels
    gaussian_pass_num: int = 5,  # number of gaussian passes
):
    n_row, n_col = img.shape

    fake_white = np.random.randint(
        low=beam_low,
        high=beam_high,
        size=(n_row, n_col),
        dtype=img.dtype,
    )

    loc_pk1 = (int(n_row / 2), int(n_col / 4))
    loc_pk2 = (int(n_row / 2), int(n_col / 4) * 3)

    fake_white[loc_pk1[0] - beam_height : loc_pk1[0] + beam_height, loc_pk1[1]] = np.iinfo(img.dtype).max
    fake_white[loc_pk2[0] - beam_height : loc_pk2[0] + beam_height, loc_pk2[1]] = np.iinfo(img.dtype).max

    # mimic the beam profile from HIFR
    for _ in range(gaussian_pass_num):
        fake_white = gaussian_filter(fake_white, sigma=beam_height / 2)

    return fake_white


def prepare_synthetic_data():
    """prepare synthetic whites, darks, raw, and reference proj"""
    np.random.seed(7)
    # input image (reference)
    img = skimage.data.brain()[7, :, :]
    # bad pixels
    num_bad_pixels = 7
    bad_pixels = np.random.randint(
        low=0,
        high=img.shape[0],
        size=(num_bad_pixels, 2),
    )
    # generage fake darks and whites
    num_dark = 10
    num_white = 10
    darks = np.array([generate_fake_darkfield(img, bad_pixels) for _ in range(num_dark)]).reshape(num_dark, *img.shape)
    whites = np.array([generate_fake_whitefield(img) for _ in range(num_white)]).reshape(num_white, *img.shape)
    # make synthetic projections (normalized) and raw image (non-normalized)
    proj = 1.0 - img / np.iinfo(img.dtype).max
    dark = np.median(darks, axis=0)
    white = np.median(whites, axis=0)
    raw = proj * (white - dark) + dark
    return raw, darks, whites, proj


def test_normalization_standard():
    """standard normalization routine with reasonable dark and white."""
    raw, darks, whites, proj = prepare_synthetic_data()
    # process with normalization
    proj_imars3d = normalization(raw, whites, darks)
    # compare
    diff = np.absolute(proj_imars3d - proj).sum() / np.prod(proj.shape)
    assert diff < 0.01


def test_normalization_bad_dark():
    """normalization routine where dark contains pixels that has higher counts
    than white due to hardware defect.
    """
    raw, darks, whites, proj = prepare_synthetic_data()
    # randomly select one pixel in dark to have higher counts than white
    for i in range(darks.shape[0]):
        ix, iy = np.random.randint(low=0, high=darks.shape[1], size=2)
        darks[i, ix, iy] += whites[i, ix, iy]
    # process with normalization
    proj_imars3d = normalization(raw, whites, darks)
    # compare
    diff = np.absolute(proj_imars3d - proj).sum() / np.prod(proj.shape)
    assert diff < 0.01


if __name__ == "__main__":
    pytest.main("( __file__")
