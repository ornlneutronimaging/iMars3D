#!/usr/bin/env python3
# package imports
from imars3d.backend.preparation.normalization import minus_log, normalization
from imars3d.backend.workflow.engine import WorkflowEngineAuto

# third party imports
import numpy as np
import pytest
from scipy.ndimage import gaussian_filter
import skimage

# standard library
import json
from pathlib import Path


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


def generate_fake_flatfield(
    img: np.ndarray,  # reference image
    beam_low: int = 15_000,  # incident beam intensity lower bound (counts)
    beam_high: int = 35_000,  # incident beam intensity upper bound (counts)
    beam_height: int = 30,  # incident beam height in pixels
    gaussian_pass_num: int = 5,  # number of gaussian passes
):
    n_row, n_col = img.shape

    fake_flat = np.random.randint(
        low=beam_low,
        high=beam_high,
        size=(n_row, n_col),
        dtype=img.dtype,
    )

    loc_pk1 = (int(n_row / 2), int(n_col / 4))
    loc_pk2 = (int(n_row / 2), int(n_col / 4) * 3)

    fake_flat[loc_pk1[0] - beam_height : loc_pk1[0] + beam_height, loc_pk1[1]] = np.iinfo(img.dtype).max
    fake_flat[loc_pk2[0] - beam_height : loc_pk2[0] + beam_height, loc_pk2[1]] = np.iinfo(img.dtype).max

    # mimic the beam profile from HIFR
    for _ in range(gaussian_pass_num):
        fake_flat = gaussian_filter(fake_flat, sigma=beam_height / 2)

    return fake_flat


def prepare_synthetic_data():
    """prepare synthetic flats, darks, raw, and reference proj"""
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
    # generage fake darks and flats
    num_dark = 10
    num_flat = 10
    darks = np.array([generate_fake_darkfield(img, bad_pixels) for _ in range(num_dark)]).reshape(num_dark, *img.shape)
    flats = np.array([generate_fake_flatfield(img) for _ in range(num_flat)]).reshape(num_flat, *img.shape)
    # make synthetic projections (normalized) and raw image (non-normalized)
    proj = 1.0 - img / np.iinfo(img.dtype).max
    dark = np.median(darks, axis=0)
    flat = np.median(flats, axis=0)
    raw = proj * (flat - dark) + dark
    return raw, darks, flats, proj


def test_normalization_standard():
    """standard normalization routine with reasonable dark and flat."""
    raw, darks, flats, proj = prepare_synthetic_data()
    # process with normalization
    proj_imars3d = normalization(arrays=raw, flats=flats, darks=darks)
    # compare
    diff = np.absolute(proj_imars3d - proj).sum() / np.prod(proj.shape)
    assert diff < 0.01


def test_normalization_bright_dark():
    """normalization routine where dark contains pixels that has higher counts
    than flat due to hardware defect.
    """
    raw, darks, flats, proj = prepare_synthetic_data()
    # randomly select one pixel in dark to have higher counts than flat
    for i in range(darks.shape[0]):
        ix, iy = np.random.randint(low=0, high=darks.shape[1], size=2)
        darks[i, ix, iy] += flats[i, ix, iy]
    # process with normalization
    proj_imars3d = normalization(arrays=raw, flats=flats, darks=darks)
    # compare
    diff = np.absolute(proj_imars3d - proj).sum() / np.prod(proj.shape)
    assert diff < 0.01


def test_normalization_no_darks():
    """Test normalization routine without providing dark field images."""
    raw, _, flats, proj = prepare_synthetic_data()

    # Process with normalization, passing None for darks
    proj_imars3d = normalization(arrays=raw, flats=flats, darks=None)

    # Compare results
    diff = np.absolute(proj_imars3d - proj).sum() / np.prod(proj.shape)
    assert diff < 0.02  # Increased tolerance from 0.01 to 0.02 to account for the lack of dark field images

    # Additional check: Ensure the shape of the output matches the input
    assert proj_imars3d.shape == raw.shape

    # Check that values are within expected range (0 to 1 for normalized data)
    assert np.all(proj_imars3d >= 0) and np.all(proj_imars3d <= 1)


class TestMinusLog:
    @pytest.mark.parametrize("ncore", [1, 2])
    def test_execution(self, ncore: int) -> None:
        r"""Invoke minus_log on a simple array with different number of processing cores"""
        arrays = 42 * np.ones(6).reshape((1, 2, 3))
        arrays_normalized = minus_log(arrays=arrays, max_workers=ncore)
        np.testing.assert_allclose(arrays_normalized, -np.log(arrays), atol=1.0e-3)

    def test_dryrun(self, JSON_DIR: Path) -> None:
        r"""Validate a JSON file containing a minus_log task"""
        task = json.loads(
            """
        {
            "name": "minus_log",
            "function": "imars3d.backend.preparation.normalization.minus_log",
            "inputs": {"arrays": "ct", "max_workers": 2},
            "outputs": ["ct"]
        }"""
        )
        config = json.load(open(JSON_DIR / "good_non_interactive_full.json"))
        config["tasks"].insert(6, task)  # insert minus_log task after normalization
        workflow = WorkflowEngineAuto(config)
        workflow._dryrun()

    def test_exception(self) -> None:
        r"""Applying minus_log to an array with elements equal or smaller than zero should raise ValueError"""
        with pytest.raises(ValueError) as e:
            minus_log(arrays=1.0 * np.arange(42), max_workers=1)
        assert "'minus_log' cannot be applied" in str(e.value)


if __name__ == "__main__":
    pytest.main([__file__])
