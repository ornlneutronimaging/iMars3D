#!/usr/bin/env python3
import numpy as np
import pytest
import tomopy
from imars3dv2.filters.intensity_fluctuation_correction import intensity_fluctuation_correction

np.random.seed(0)


def generate_fake_projections(
    n_projections: int = 1440,
) -> np.ndarray:
    # create the synthetic object
    # use default shape: 128x128x128
    shepp3d = tomopy.misc.phantom.shepp3d()
    # create the projections (1440 -> 0.25 deg step)
    omegas = np.linspace(0, np.pi * 2, n_projections)
    radiograph_stack = tomopy.sim.project.project(shepp3d, omegas, emission=False)
    return radiograph_stack


def generate_fake_flatfield(
    radiograph: np.ndarray,
    intensity_average: int,
    dynamic_range: int,
) -> np.ndarray:
    # calculate bound
    low_bound = max(1_000, intensity_average - dynamic_range / 2)
    high_bound = min(65_000, intensity_average + dynamic_range / 2)
    # generate a flatfield
    flat = np.random.randint(
        low=low_bound,
        high=high_bound,
        size=radiograph.shape,
    )
    #
    return flat


def generate_flickering_projections(
    projections_ideal: np.ndarray,
) -> np.ndarray:
    # make a fake fluctuating beam intensity profile
    n_projections = projections_ideal.shape[0]
    x = np.linspace(0, 0.5, int(n_projections / 2))
    x = np.vstack((x, x)).flatten()
    intensity = (-(x**2) + 1) * 50_000
    dynamic_range = 20_000
    # make flats
    flats = np.array(
        [generate_fake_flatfield(projections_ideal[0], intensity[i], dynamic_range) for i in range(n_projections)]
    )
    # make it flickering
    projections = projections_ideal * flats
    # pretend the projections has gone through the regular flatfield correction
    flat_avg = np.mean(flats, axis=0)
    projections = projections / flat_avg
    return projections


def test_correct_with_tomopy():
    # get synthetic projections
    projs_ideal = generate_fake_projections()
    # generate the corresponding flickering projections
    projs_flickering = generate_flickering_projections(projs_ideal)
    # perform correction
    projs_corrected = intensity_fluctuation_correction(projs_flickering, air_pixels=5)
    # verify
    # NOTE: after the correction, the air region within each sinogram should be
    #       close to uniform, therefore should result in smaller variance when
    #       compared with the ideal one.
    diff_raw = projs_flickering - projs_ideal
    diff_corrected = projs_corrected - projs_ideal
    assert diff_corrected.var() < diff_raw.var()


def test_correct_with_imars3d():
    # get synthetic projections
    projs_ideal = generate_fake_projections()
    # generate the corresponding flickering projections
    projs_flickering = generate_flickering_projections(projs_ideal)
    # perform correction with skimage
    projs_corrected = intensity_fluctuation_correction(projs_flickering, air_pixels=-1)
    # verify
    diff_raw = projs_flickering - projs_ideal
    diff_corrected = projs_corrected - projs_ideal
    assert diff_corrected.var() < diff_raw.var()


def test_incorrect_input_array():
    projs_incorrect = np.array([1, 2, 3])
    with pytest.raises(ValueError):
        intensity_fluctuation_correction(projs_incorrect, air_pixels=5)


if __name__ == "__main__":
    pytest.main([__file__])
