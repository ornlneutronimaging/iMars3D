# package imports
from imars3d.backend.util.functions import clamp_max_workers, to_time_str

# third party imports
import pytest

# standard imports
from datetime import datetime


def test_clamp_max_workers():
    assert clamp_max_workers(10) >= 1
    assert clamp_max_workers(-10) >= 1


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
