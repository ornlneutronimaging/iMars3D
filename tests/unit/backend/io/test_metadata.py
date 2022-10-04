#!/usr/bin/env python3
"""
Unit tests for backend metadata auxiliary class.
"""
import os
import pytest
import numpy as np
import tifffile
from imars3d.backend.io.metadata import MetaData
from imars3d.backend.io.metadata import _extract_metadata_from_tiff


@pytest.fixture(scope="module")
def test_data():
    # create testing tiff images
    data = np.ones((3, 3))
    #
    ext_tags_ct = [
        (65026, "s", 0, "ManufacturerStr:Test", True),
        (65027, "s", 0, "ExposureTime:70.000000", True),
        (65068, "s", 0, "MotSlitHR.RBV:10.000000", True),
        (65070, "s", 0, "MotSlitHL.RBV:20.000000", True),
        (65066, "s", 0, "MotSlitVT.RBV:10.000000", True),
        (65068, "s", 0, "MotSlitHR.RBV:10.000000", True),
    ]
    ext_tags_dc = [
        (65026, "s", 0, "ManufacturerStr:Test", True),
        (65027, "s", 0, "ExposureTime:70.000000", True),
    ]
    ext_tags_ct_alt = [
        (65026, "s", 0, "ManufacturerStr:Test", True),
        (65027, "s", 0, "ExposureTime:71.000000", True),
        (65068, "s", 0, "MotSlitHR.RBV:11.000000", True),
        (65070, "s", 0, "MotSlitHL.RBV:21.000000", True),
        (65066, "s", 0, "MotSlitVT.RBV:11.000000", True),
        (65068, "s", 0, "MotSlitHR.RBV:11.000000", True),
    ]
    # write testing data
    tifffile.imwrite("test_ct.tiff", data, extratags=ext_tags_ct)
    tifffile.imwrite("test_ob.tiff", data, extratags=ext_tags_ct)
    tifffile.imwrite("test_dc.tiff", data, extratags=ext_tags_dc)
    tifffile.imwrite("test_ct_alt.tiff", data, extratags=ext_tags_ct_alt)
    yield
    # cleanup
    os.remove("test_ct.tiff")
    os.remove("test_ob.tiff")
    os.remove("test_dc.tiff")
    os.remove("test_ct_alt.tiff")


def test_metadata(test_data):
    metadata_ct = MetaData(filename="test_ct.tiff", datatype="ct")
    metadata_ob = MetaData(filename="test_ob.tiff", datatype="ob")
    metadata_dc = MetaData(filename="test_dc.tiff", datatype="dc")
    metadata_ct_alt = MetaData(filename="test_ct_alt.tiff", datatype="ct")
    # ct and ob, dc should match
    assert metadata_ct == metadata_ob
    assert metadata_ct == metadata_dc
    assert metadata_ct.match(other_filename="test_ob.tiff", other_datatype="ob")
    assert metadata_ct.match(other_filename="test_dc.tiff", other_datatype="dc")
    # ct_alt and ob, dc should not match
    assert metadata_ct != metadata_ct_alt
    assert metadata_ct_alt != metadata_ob
    assert metadata_ct_alt != metadata_dc
    assert not metadata_ct_alt.match(other_filename="test_ob.tiff", other_datatype="ob")
    assert not metadata_ct_alt.match(other_filename="test_dc.tiff", other_datatype="dc")


def test_extract_metadata_from_tiff(test_data):
    test_filename = "test_ct.tiff"
    test_index = [65026, 65027]
    #
    ref = {"ManufacturerStr": "Test", "ExposureTime": 70.0}
    #
    assert _extract_metadata_from_tiff(test_filename, test_index) == ref


if __name__ == "__main__":
    pytest.main([__file__])
