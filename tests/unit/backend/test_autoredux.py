#!/usr/bin/env python3
import pytest
from imars3d.backend import auto_reduction_ready
from imars3d.backend import load_template_config
from imars3d.backend import extract_info_from_path


def test_auto_reduction_ready():
    # NOTE: update the test when implement the function
    with pytest.raises(NotImplementedError):
        auto_reduction_ready(data_file="test")


def test_load_template_config():
    # NOTE: update the test when template json is created
    with pytest.raises(FileNotFoundError):
        load_template_config("")


def test_extract_info_from_path():
    # NOTE: update the test when implement the function
    with pytest.raises(NotImplementedError):
        extract_info_from_path(data_file="test")


if __name__ == "__main__":
    pytest.main([__file__])
