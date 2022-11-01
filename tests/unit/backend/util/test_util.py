import pytest
from imars3d.backend.util.util import clamp_max_workers


def test_clamp_max_workers():
    assert clamp_max_workers(10) >= 1
    assert clamp_max_workers(-10) >= 1
