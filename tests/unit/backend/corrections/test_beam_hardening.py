"""Unit test for beam hardening correction"""
#!/usr/bin/env python
import numpy as np
import pytest
from imars3d.backend.corrections.beam_hardening import beam_hardening_correction


@pytest.fixture(scope="module")
def fake_beam_hardening_image() -> np.ndarray:
    """Use a checker board image as the fake beam hardening image

    Returns
    -------
    np.ndarray
        A checker board image stack

    NOTE
    ----
    As of 02-15-2024, the dev team did not receive needed testing data
    for beam hardening correction, a synthetic image is used for testing.
    """
    np.random.seed(42)
    image_stack = []
    image_size = 255
    image = np.zeros((image_size, image_size))
    for i in range(image_size):
        for j in range(image_size):
            if (i + j) % 2 == 0:
                image[i, j] = 1
    # flip the image to create a stack
    for _ in range(10):
        if np.random.rand() > 0.5:
            image = np.flip(image, axis=0)
        else:
            image = np.flip(image, axis=1)
        image_stack.append(image)
    return np.stack(image_stack, axis=0)


def test_beam_hardening_correction(fake_beam_hardening_image):
    """Test beam hardening correction"""
    # test the correction
    corrected_image = beam_hardening_correction(
        arrays=fake_beam_hardening_image,
        q=0.005,
        n=20.0,
        opt=True,
    )
    assert corrected_image.shape == (10, 255, 255)
    assert corrected_image.dtype == np.float64
    assert np.all(corrected_image >= 0)


if __name__ == "__main__":
    pytest.main([__file__])
