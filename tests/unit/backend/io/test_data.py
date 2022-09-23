#!/usr/bin/env python3
"""
Unit tests for backend data loading.
"""

import os
import glob
import pytest
import astropy.io.fits as fits
import tifffile
import numpy as np
from functools import partial
from unittest import mock
from pathlib import Path
from imars3d.backend.io.data import load_data
from imars3d.backend.io.data import _forgiving_reader
from imars3d.backend.io.data import _load_images
from imars3d.backend.io.data import _load_by_file_list
from imars3d.backend.io.data import _get_filelist_by_dir
from imars3d.backend.io.data import _extract_rotation_angles


@pytest.fixture(scope="module")
def test_data():
    # create some test data
    data = np.ones((3, 3))
    # -- good tiff name, no need for meatdata
    tifffile.imwrite("test.tiff", data)
    # -- good tiff with good name, no metadata
    tifffile.imwrite("20191030_expname_0080_010_020_1960.tiff", data)
    # -- bad tiff name, but with metadata
    ex_tags = [
        (65039, "s", 0, "RotationActual:0.1", True),
    ]
    for i in range(3):
        tifffile.imwrite(
            f"test_with_metadata_{i}.tiff",
            data,
            extratags=ex_tags,
        )

    # synthetic fits data
    hdu = fits.PrimaryHDU(data)
    hdu.writeto("test.fits")
    yield

    # remove the test data
    list(map(os.remove, map(str, glob.glob("*.tiff"))))
    list(map(os.remove, map(str, glob.glob("*.fits"))))


@mock.patch("imars3d.backend.io.data._extract_rotation_angles", return_value=4)
@mock.patch("imars3d.backend.io.data._get_filelist_by_dir", return_value=("1", "2", "3"))
@mock.patch("imars3d.backend.io.data._load_by_file_list", return_value=(1, 2, 3))
def test_load_data(_load_by_file_list, _get_filelist_by_dir, _extract_rotation_angles):
    # error_0: incorrect input argument types
    with pytest.raises(ValueError):
        load_data(ct_files=1, ob_files=[], dc_files=[])
        load_data(ct_files=[], ob_files=[], dc_files=[], ct_fnmatch=1)
        load_data(ct_files=[], ob_files=[], dc_files=[], ob_fnmatch=1)
        load_data(ct_files=[], ob_files=[], dc_files=[], dc_fnmatch=1)
        load_data(ct_files=[], ob_files=[], dc_files=[], max_workers="x")
        load_data(ct_dir=1, ob_dir="/tmp", dc_dir="/tmp")
        load_data(ct_dir="/tmp", ob_dir=1, dc_dir="/tmp")
    # error_1: out of bounds value
    with pytest.raises(ValueError):
        load_data(ct_files=[], ob_files=[], dc_files=[], max_workers=-1)
    # error_2: mix usage of function signature 1 and 2
    with pytest.raises(ValueError):
        load_data(ct_files=[], ob_files=[], dc_files=[], ct_dir="/tmp", ob_dir="/tmp")
    # case_1: load data from file list
    rst = load_data(ct_files=["1", "2"], ob_files=["3", "4"], dc_files=["5", "6"])
    assert rst == (1, 2, 3, 4)
    # case_2: load data from given directory
    rst = load_data(ct_dir="/tmp", ob_dir="/tmp", dc_dir="/tmp")
    assert rst == (1, 2, 3, 4)


def test_forgiving_reader():
    # correct usage
    goodReader = lambda x: x
    assert _forgiving_reader(filename="test", reader=goodReader) == "test"
    # incorrect usage, but bypass the exception
    badReader = lambda x: x / 0
    assert _forgiving_reader(filename="test", reader=badReader) is None


def test_load_images(test_data):
    func = partial(_load_images, desc="test", max_workers=2)
    # error case: unsupported file format
    incorrect_filelist = ["file1.bad", "file2.bad"]
    with pytest.raises(ValueError):
        rst = func(filelist=incorrect_filelist)
    # case1: tiff
    tiff_filelist = ["test.tiff", "test.tiff"]
    rst = func(filelist=tiff_filelist)
    assert rst.shape == (2, 3, 3)
    # case2: fits
    fits_filelist = ["test.fits", "test.fits"]
    rst = func(filelist=fits_filelist)
    assert rst.shape == (2, 3, 3)


@mock.patch("imars3d.backend.io.data._load_images", return_value="a")
def test_load_by_file_list(_load_images):
    # error_1: ct empty
    with pytest.raises(ValueError):
        _load_by_file_list(ct_files=[], ob_files=[])
    # error_2: ob empty
    with pytest.raises(ValueError):
        _load_by_file_list(ct_files=["dummy"], ob_files=[])
    # case_1: load all three
    rst = _load_by_file_list(ct_files=["a.tiff"], ob_files=["a.tiff"], dc_files=["a.tiff"])
    assert rst == ("a", "a", "a")
    # case_2: load only ct and ob
    rst = _load_by_file_list(ct_files=["a.tiff"], ob_files=["a.tiff"])
    assert rst == ("a", "a", None)


def test_get_filelist_by_dir(test_data):
    # error_1: ct_dir does not exists
    with pytest.raises(ValueError):
        _get_filelist_by_dir(ct_dir="dummy", ob_dir="/tmp", dc_dir="/tmp")
    # error_2: ob_dir does not exists
    with pytest.raises(ValueError):
        _get_filelist_by_dir(ct_dir="/tmp", ob_dir="dummy", dc_dir="/tmp")
    # case_1: load all three
    cwd = Path.cwd()
    fnpattern = "*.tiff"
    ref = list(map(str, cwd.glob(fnpattern)))
    rst = _get_filelist_by_dir(
        ct_dir=str(cwd),
        ob_dir=str(cwd),
        dc_dir=str(cwd),
        ct_fnmatch=fnpattern,
        ob_fnmatch=fnpattern,
        dc_fnmatch=fnpattern,
    )
    assert rst == (ref, ref, ref)
    # case_2: load ct and ob, skipping dc
    rst = _get_filelist_by_dir(
        ct_dir=str(cwd),
        ob_dir=str(cwd),
        ct_fnmatch=fnpattern,
        ob_fnmatch=fnpattern,
        dc_fnmatch=fnpattern,
    )
    assert rst == (ref, ref, [])
    # case_2: load ct, and detect ob and df from metadata
    # TODO: once the FileMetaData class is ready, we can start
    # case_3: load ct, and detect ob from metadata
    # TODO: once the FileMetaData class is ready, we can start


def test_extract_rotation_angles(test_data):
    # error_1: empty list
    with pytest.raises(ValueError):
        _extract_rotation_angles([])
    # error_2: unsupported file format for extracting from metadata
    with pytest.raises(ValueError):
        _extract_rotation_angles(["dummy.dummier", "dummy.dummier"])
    # case_1: extract from filename
    fn = "20191030_expname_0080_010_020_1960.tiff"
    rst = _extract_rotation_angles([fn, fn])
    ref = np.array([10.02, 10.02])
    np.testing.assert_array_almost_equal(rst, ref)
    # case_2: extract from metadata
    fnl = [f"test_with_metadata_{i}.tiff" for i in range(3)]
    rst = _extract_rotation_angles(fnl)
    ref = np.array([0.1, 0.1, 0.1])
    np.testing.assert_array_almost_equal(rst, ref)


if __name__ == "__main__":
    pytest.main([__file__])
