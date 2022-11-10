#!/usr/bin/env python3
import pytest
from imars3d.backend import auto_reduction_ready
from imars3d.backend import load_template_config
from imars3d.backend import extract_info_from_path

TIFF_DIR = "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man"

def test_auto_reduction_ready():
    # NOTE: update the test when implement the function
    with pytest.raises(NotImplementedError):
        auto_reduction_ready(data_file="test")


def test_load_template_config():
    # NOTE: update the test when template json is created
    with pytest.raises(FileNotFoundError):
        _ = load_template_config("")

def test_extract_from_path(self):
    data = extract_info_from_path(TIFF_DIR)
    assert data["facility"] == "HFIR"
    assert data["instrument"] == "CG1D"
    assert data["ipts"] == "IPTS-25777"


if __name__ == "__main__":
    pytest.main([__file__])
