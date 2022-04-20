#!/usr/bin/env python3
import numpy as np
import pytest
import skimage
from imars3dv2.filters.gamma_filter import gamma_filter


@pytest.mark.parametrize(
    "use_selective_median_filter,unchanged_pixels",
    [
        (False, ()),
        (True, ([0, 0], [124, 124])),
    ],
)
def test_gamma_filter(use_selective_median_filter, unchanged_pixels):
    """ """
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
    #
    saturation_intensity = np.iinfo(imgs_with_noise.dtype).max
    for i, j in NOISE_LOC:
        imgs_with_noise[0, j, i] = saturation_intensity - np.random.randint(0, 4)
    # call gamma_filter
    imgs_filtered = gamma_filter(imgs_with_noise, selective_median_filter=use_selective_median_filter)
    # verify results
    for i, j in NOISE_LOC:
        # all the artificial gamma saturated pixels should be replaced
        # with meaningful values (i.e. not saturated)
        assert imgs_filtered[0, j, i] < saturation_intensity - 4

    for i, j in unchanged_pixels:
        assert imgs_filtered[0, j, i] == imgs_reference[0, j, i]


if __name__ == "__main__":
    pytest.main("( __file__")
