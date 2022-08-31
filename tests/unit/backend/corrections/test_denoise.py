#!/usr/bin/env python3
import numpy as np
import pytest
import skimage
from unittest import mock
from skimage.util import random_noise

from imars3d.backend.corrections.denoise import measure_noiseness
from imars3d.backend.corrections.denoise import measure_sharpness
from imars3d.backend.corrections.denoise import denoise
from imars3d.backend.corrections.denoise import denoise_by_median
from imars3d.backend.corrections.denoise import denoise_by_bilateral
from imars3d.backend.corrections.denoise import denoise_by_bilateral_2d


np.random.seed(0)


def generate_fake_noisy_image(
    mode: str = "speckle",
    noise_var: float = 1e-4,
) -> np.ndarray:
    # create a fake CT absorption graph
    img_ref = skimage.data.brain()[0]
    img_ref = np.iinfo(img_ref.dtype).max - img_ref
    # add noise
    img_noisy = random_noise(img_ref, mode=mode, var=noise_var) * np.iinfo(img_ref.dtype).max
    return img_ref, img_noisy


def test_measure_noiseness():
    img_ref, img_noisy = generate_fake_noisy_image()
    noiseness_ref = measure_noiseness(img_ref)
    noiseness_noisy = measure_noiseness(img_noisy)
    assert noiseness_ref < noiseness_noisy


def test_measure_sharpness():
    img_ref, img_noisy = generate_fake_noisy_image()
    sharpness_ref = measure_sharpness(img_ref)
    sharpness_noisy = measure_sharpness(img_noisy)
    # noises are very sharp, so a noisy image will generall have a higher
    # sharpness than the reference image
    assert sharpness_ref < sharpness_noisy


@mock.patch("imars3d.backend.corrections.denoise.denoise_by_median")
@mock.patch("imars3d.backend.corrections.denoise.denoise_by_bilateral")
def test_denoise(mock_denoise_by_bilateral, mock_denoise_by_median):
    _, img_noisy = generate_fake_noisy_image()
    # test call to median method
    denoise(img_noisy, method="median")
    mock_denoise_by_median.assert_called_once()
    # test call to bilateral method
    denoise(img_noisy, method="bilateral")
    mock_denoise_by_bilateral.assert_called_once()
    # test call to invalid method
    with pytest.raises(ValueError):
        denoise(img_noisy, method="invalid")


def test_denoise_by_median():
    _, img_noisy = generate_fake_noisy_image()
    noise_level_noisy = measure_noiseness(img_noisy)
    # 2D image case
    img_denoised = denoise_by_median(img_noisy)
    noise_level_denoised = measure_noiseness(img_denoised)
    assert noise_level_noisy > noise_level_denoised
    # 3D image stack case
    _, img_noisy = generate_fake_noisy_image()
    imgstack_noisy = np.stack([img_noisy] * 10, axis=0)
    imgstack_denoised = denoise_by_median(imgstack_noisy)
    noise_level_denoised = measure_noiseness(imgstack_denoised[0])
    assert noise_level_noisy > noise_level_denoised
    # invalide image stack case
    with pytest.raises(ValueError):
        denoise_by_median(np.array([1, 2, 3]))


def test_denoise_by_bilateral():
    # NOTE:
    # the bilateral image does not dramatically reduce the noise level metric,
    # but it does provide a somewhat cleaner image.
    _, img_noisy = generate_fake_noisy_image()
    noise_level_noisy = measure_noiseness(img_noisy)
    # 2d image case
    img_denoised = denoise_by_bilateral(img_noisy)
    noise_level_denoised = measure_noiseness(img_denoised)
    np.testing.assert_almost_equal(noise_level_noisy, noise_level_denoised, decimal=3)
    # 3D image stack case
    _, img_noisy = generate_fake_noisy_image()
    imgstack_noisy = np.stack([img_noisy] * 10, axis=0)
    imgstack_denoised = denoise_by_bilateral(imgstack_noisy)
    noise_level_noisy = measure_noiseness(imgstack_noisy[0])
    noise_level_denoised = measure_noiseness(imgstack_denoised[0])
    np.testing.assert_almost_equal(noise_level_noisy, noise_level_denoised, decimal=3)
    # invalid image stack case
    with pytest.raises(ValueError):
        denoise_by_bilateral(np.array([1, 2, 3]))


def test_denoise_by_bilateral_2d():
    _, img_noisy = generate_fake_noisy_image()
    noise_level_noisy = measure_noiseness(img_noisy)
    img_denoised = denoise_by_bilateral_2d(img_noisy)
    noise_level_denoised = measure_noiseness(img_denoised)
    np.testing.assert_almost_equal(noise_level_noisy, noise_level_denoised, decimal=3)


if __name__ == "__main__":
    pytest.main([__file__])
