#!/usr/bin/env python3
"""
Unit tests for backend metadata auxiliary class.
"""
# package imports
from imars3d.backend.dataio.metadata import _extract_metadata_from_tiff
from imars3d.backend.dataio.metadata import MetaData

# third party imports
import pytest
import numpy as np
import tifffile


@pytest.fixture(scope="function")
def data_fixture(tmpdir):
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
    ct = tmpdir / "ct_dir" / "test_ct.tiff"
    ct.parent.mkdir()
    tifffile.imwrite(str(ct), data, extratags=ext_tags_ct)
    ob = tmpdir / "ob_dir" / "test_ob.tiff"
    ob.parent.mkdir()
    tifffile.imwrite(str(ob), data, extratags=ext_tags_ct)
    dc = tmpdir / "dc_dir" / "test_dc.tiff"
    dc.parent.mkdir()
    tifffile.imwrite(str(dc), data, extratags=ext_tags_dc)
    ct_alt = tmpdir / "ct_alt_dir" / "test_ct_alt.tiff"
    ct_alt.parent.mkdir()
    tifffile.imwrite(str(ct_alt), data, extratags=ext_tags_ct_alt)
    # for extension checking
    fits = tmpdir / "fits_dir" / "test.fits"
    fits.parent.mkdir()
    tifffile.imwrite(str(fits), data)
    return ct, ob, dc, ct_alt, fits


def test_metadata(data_fixture):
    ct, ob, dc, ct_alt, _ = list(map(str, data_fixture))
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


def test_not_implemented(data_fixture):
    ct, ob, dc, ct_alt, fits = list(map(str, data_fixture))
    with pytest.raises(ValueError):
        MetaData(filename=fits, datatype="ct")
    #
    metadata_ct = MetaData(filename=ct, datatype="ct")
    with pytest.raises(ValueError):
        metadata_ct.match(other_filename=fits, other_datatype="ct")


def test_extract_metadata_from_tiff(data_fixture):
    ct, ob, dc, ct_alt, fits = list(map(str, data_fixture))
    test_filename = ct
    test_index = [65026, 65027]
    #
    ref = {"ManufacturerStr": "Test", "ExposureTime": 70.0}
    #
    assert _extract_metadata_from_tiff(test_filename, test_index) == ref


if __name__ == "__main__":
    pytest.main([__file__])
