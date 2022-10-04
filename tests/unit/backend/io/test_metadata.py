#!/usr/bin/env python3
"""
Unit tests for backend metadata auxiliary class.
"""
import pytest
import numpy as np
import tifffile
from imars3d.backend.io.metadata import MetaData
from imars3d.backend.io.metadata import _extract_metadata_from_tiff


@pytest.fixture(scope="module")
def test_data(tmpdir_factory):
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
    ct = tmpdir_factory.mktemp("test_metadata").join("test_ct.tiff")
    tifffile.imwrite(str(ct), data, extratags=ext_tags_ct)
    ob = tmpdir_factory.mktemp("test_metadata").join("test_ob.tiff")
    tifffile.imwrite(str(ob), data, extratags=ext_tags_ct)
    dc = tmpdir_factory.mktemp("test_metadata").join("test_dc.tiff")
    tifffile.imwrite(str(dc), data, extratags=ext_tags_dc)
    ct_alt = tmpdir_factory.mktemp("test_metadata").join("test_ct_alt.tiff")
    tifffile.imwrite(str(ct_alt), data, extratags=ext_tags_ct_alt)
    # for extension checking
    fits = tmpdir_factory.mktemp("test_metadata").join("test.fits")
    tifffile.imwrite(str(fits), data)
    return ct, ob, dc, ct_alt, fits


def test_metadata(test_data):
    ct, ob, dc, ct_alt, _ = list(map(str, test_data))
    metadata_ct = MetaData(filename=ct, datatype="ct")
    metadata_ob = MetaData(filename=ob, datatype="ob")
    metadata_dc = MetaData(filename=dc, datatype="dc")
    metadata_ct_alt = MetaData(filename=ct_alt, datatype="ct")
    # ct and ob, dc should match
    assert metadata_ct == metadata_ob
    assert metadata_ct == metadata_dc
    assert metadata_ct.match(other_filename=ob, other_datatype="ob")
    assert metadata_ct.match(other_filename=dc, other_datatype="dc")
    # ct_alt and ob, dc should not match
    assert metadata_ct != metadata_ct_alt
    assert metadata_ct_alt != metadata_ob
    assert metadata_ct_alt != metadata_dc
    assert not metadata_ct_alt.match(other_filename=ob, other_datatype="ob")
    assert not metadata_ct_alt.match(other_filename=dc, other_datatype="dc")


def test_not_implemented(test_data):
    ct, ob, dc, ct_alt, fits = list(map(str, test_data))
    with pytest.raises(ValueError):
        MetaData(filename=fits, datatype="ct")
    #
    metadata_ct = MetaData(filename=ct, datatype="ct")
    with pytest.raises(ValueError):
        metadata_ct.match(other_filename=fits, other_datatype="ct")


def test_extract_metadata_from_tiff(test_data):
    ct, ob, dc, ct_alt, fits = list(map(str, test_data))
    test_filename = ct
    test_index = [65026, 65027]
    #
    ref = {"ManufacturerStr": "Test", "ExposureTime": 70.0}
    #
    assert _extract_metadata_from_tiff(test_filename, test_index) == ref


if __name__ == "__main__":
    pytest.main([__file__])
