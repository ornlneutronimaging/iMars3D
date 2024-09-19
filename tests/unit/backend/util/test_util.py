# package imports
from imars3d.backend.util.functions import clamp_max_workers, to_time_str, calculate_chunksize

# third party imports
import pytest
from unittest.mock import patch

# standard imports
from datetime import datetime


def test_clamp_max_workers():
    assert clamp_max_workers(10) >= 1
    assert clamp_max_workers(-10) >= 1


@patch("multiprocessing.cpu_count", return_value=8)
def test_chunksize_with_small_number_of_elements(mock_cpu_count):
    num_elements = 10
    max_workers = None
    chunksize = calculate_chunksize(num_elements, max_workers)
    assert chunksize == 1


@patch("multiprocessing.cpu_count", return_value=8)
def test_chunksize_with_large_number_of_elements(mock_cpu_count):
    num_elements = 10000
    max_workers = None
    chunksize = calculate_chunksize(num_elements, max_workers)
    expected_chunksize = max(1, num_elements // (6 * 4))  # 6 workers, scale factor 4
    assert chunksize == expected_chunksize


@patch("multiprocessing.cpu_count", return_value=4)
def test_chunksize_with_different_cpu_count(mock_cpu_count):
    num_elements = 10000
    max_workers = None
    chunksize = calculate_chunksize(num_elements, max_workers)
    expected_chunksize = max(1, num_elements // (2 * 4))  # 2 workers (cpu_count - 2), scale factor 4
    assert chunksize == expected_chunksize


@patch("multiprocessing.cpu_count", return_value=8)
def test_chunksize_with_max_workers(mock_cpu_count):
    num_elements = 10000
    max_workers = 4
    chunksize = calculate_chunksize(num_elements, max_workers)
    expected_chunksize = max(1, num_elements // (4 * 4))  # 4 workers manually set
    assert chunksize == expected_chunksize


@patch("multiprocessing.cpu_count", return_value=8)
def test_chunksize_with_custom_scale_factor(mock_cpu_count):
    num_elements = 10000
    max_workers = None
    scale_factor = 2
    chunksize = calculate_chunksize(num_elements, max_workers, scale_factor=scale_factor)
    expected_chunksize = max(1, num_elements // (6 * 2))  # 6 workers, scale factor 2
    assert chunksize == expected_chunksize


@pytest.mark.parametrize(
    "timestamp",
    [
        datetime(2022, 1, 1, 1, 1),
        datetime(2022, 12, 12, 12, 12),
    ],
)
def test_time_str(timestamp):
    value = to_time_str(timestamp)
    assert isinstance(value, str)
    assert len(value) == 12
    assert int(value), "Cannot be converted to an integer"


if __name__ == "__main__":
    pytest.main([__file__])
