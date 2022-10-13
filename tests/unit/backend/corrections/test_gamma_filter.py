#!/usr/bin/env python3
import numpy as np
import pytest
import skimage
from imars3d.backend.corrections.gamma_filter import gamma_filter


@pytest.fixture(scope="module")
def data_fixture():
    # constants
    np.random.seed(7)
    # input image
    imgs_reference = skimage.data.brain()[:2, :, :]
    imgs_with_noise = np.array(imgs_reference)
    # synthetic gamma pixel location
    NOISE_LOC = (
        (174, 134),  # feature, high intensity
        (103, 136),  # feature, low intensity
        (177, 240),  # bg, weak intensity
        (217, 131),  # bg, no intensity
    )
    # unchanged_pixels
    UNCHANGED_PIXELS = ([173, 155], [152, 65])
    #
    saturation_intensity = np.iinfo(imgs_with_noise.dtype).max
    for i, j in NOISE_LOC:
        imgs_with_noise[0, j, i] = saturation_intensity - np.random.randint(0, 4)
    return imgs_reference, imgs_with_noise, NOISE_LOC, UNCHANGED_PIXELS, saturation_intensity


def test_gamma_filter_incorrect_data_type(data_fixture):
    # NOTE:
    # since we are adopting a forgiving scheme, so this code should still run
    # even if a float array is given.
    imgs_reference, imgs_with_noise, NOISE_LOC, UNCHANGED_PIXELS, saturation_intensity = data_fixture
    gamma_filter(arrays=imgs_with_noise.astype(np.float64))


@pytest.mark.parametrize(
    "use_selective_median_filter",
    [
        (False),
        (True),
    ],
)
def test_gamma_filter_selective_filtering(use_selective_median_filter, data_fixture):
    """ """
    imgs_reference, imgs_with_noise, NOISE_LOC, UNCHANGED_PIXELS, saturation_intensity = data_fixture
    # call gamma_filter
    imgs_filtered = gamma_filter(
        arrays=imgs_with_noise,
        selective_median_filter=use_selective_median_filter,
    )
    # verify results
    for i, j in NOISE_LOC:
        # all the artificial gamma saturated pixels should be replaced
        # with meaningful values (i.e. not saturated)
        assert imgs_filtered[0, j, i] < saturation_intensity - 4

    for i, j in UNCHANGED_PIXELS:
        assert imgs_filtered[0, j, i] == imgs_reference[0, j, i]


if __name__ == "__main__":
    pytest.main([__file__])
