#!/usr/bin/env python3
"""
Unit tests for backend data loading.
"""

import pytest
import astropy.io.fits as fits
import tifffile
import numpy as np
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from imars3d.backend.dataio.data import load_data
from imars3d.backend.dataio.data import save_data, save_checkpoint
from imars3d.backend.dataio.data import _forgiving_reader
from imars3d.backend.dataio.data import _load_images
from imars3d.backend.dataio.data import _load_by_file_list
from imars3d.backend.dataio.data import _get_filelist_by_dir
from imars3d.backend.dataio.data import _extract_rotation_angles


@pytest.fixture(scope="module")
def data_fixture(tmpdir_factory):
    # dummy tiff image data
    data = np.ones((3, 3))
    #
    tmpdirname = "test_data"
    # TIFF files
    # -- valid tiff with generic name, no metadata
    generic_tiff = tmpdir_factory.mktemp(tmpdirname).join("generic.tiff")
    tifffile.imwrite(str(generic_tiff), data)
    # -- valid tiff with good name for angle extraction, no metadata
    good_tiff = tmpdir_factory.mktemp(tmpdirname).join("20191030_expname_0080_010_020_1960.tiff")
    tifffile.imwrite(str(good_tiff), data)
    # -- valid tiff with generic name, but has metadata
    ex_tags = [
        (65039, "s", 0, "RotationActual:0.1", True),
    ]
    metadata_tiff = tmpdir_factory.mktemp(tmpdirname).join("metadata.tiff")
    tifffile.imwrite(str(metadata_tiff), data, extratags=ex_tags)
    # Fits files
    generic_fits = tmpdir_factory.mktemp(tmpdirname).join("generic.fits")
    hdu = fits.PrimaryHDU(data)
    hdu.writeto(str(generic_fits))
    # return the tmp files
    return generic_tiff, good_tiff, metadata_tiff, generic_fits


@mock.patch("imars3d.backend.dataio.data._extract_rotation_angles", return_value=4)
@mock.patch("imars3d.backend.dataio.data._get_filelist_by_dir", return_value=("1", "2", "3"))
@mock.patch("imars3d.backend.dataio.data._load_by_file_list", return_value=(1, 2, 3))
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
    # error_3: no valid signature found
    with pytest.raises(ValueError):
        load_data(ct_fnmatch=1)
    # case_0: load data from file list
    rst = load_data(ct_files=["1", "2"], ob_files=["3", "4"], dc_files=["5", "6"])
    assert rst == (1, 2, 3, 4)
    # case_1: load data from given directory
    rst = load_data(ct_dir="/tmp", ob_dir="/tmp", dc_dir="/tmp")
    assert rst == (1, 2, 3, 4)


def test_forgiving_reader():
    # correct usage
    goodReader = lambda x: x
    assert _forgiving_reader(filename="test", reader=goodReader) == "test"
    # incorrect usage, but bypass the exception
    badReader = lambda x: x / 0
    assert _forgiving_reader(filename="test", reader=badReader) is None


def test_load_images(data_fixture):
    generic_tiff, good_tiff, metadata_tiff, generic_fits = list(map(str, data_fixture))
    func = partial(_load_images, desc="test", max_workers=2, tqdm_class=None)
    # error_0 case: unsupported file format
    incorrect_filelist = ["file1.bad", "file2.bad"]
    with pytest.raises(ValueError):
        rst = func(filelist=incorrect_filelist)
    # case_0: tiff
    tiff_filelist = [generic_tiff, good_tiff, metadata_tiff]
    rst = func(filelist=tiff_filelist)
    assert rst.shape == (3, 3, 3)
    # case_1: fits
    fits_filelist = [generic_fits, generic_fits]
    rst = func(filelist=fits_filelist)
    assert rst.shape == (2, 3, 3)


@mock.patch("imars3d.backend.dataio.data._load_images", return_value="a")
def test_load_by_file_list(_load_images):
    # error_0: ct empty
    with pytest.raises(ValueError):
        _load_by_file_list(ct_files=[], ob_files=[])
    # error_1: ob empty
    with pytest.raises(ValueError):
        _load_by_file_list(ct_files=["dummy"], ob_files=[])
    # case_0: load all three
    rst = _load_by_file_list(ct_files=["a.tiff"], ob_files=["a.tiff"], dc_files=["a.tiff"])
    assert rst == ("a", "a", "a")
    # case_1: load only ct and ob
    rst = _load_by_file_list(ct_files=["a.tiff"], ob_files=["a.tiff"])
    assert rst == ("a", "a", None)


def test_extract_rotation_angles(data_fixture):
    generic_tiff, good_tiff, metadata_tiff, generic_fits = list(map(str, data_fixture))
    # error_0: empty list
    with pytest.raises(ValueError):
        _extract_rotation_angles([])
    # error_1: unsupported file format for extracting from metadata
    with pytest.raises(ValueError):
        _extract_rotation_angles(["dummy.dummier", "dummy.dummier"])
    # case_0: extract from filename
    rst = _extract_rotation_angles([good_tiff, good_tiff])
    ref = np.array([10.02, 10.02])
    np.testing.assert_array_almost_equal(rst, ref)
    # case_1: extract from metadata
    rst = _extract_rotation_angles([metadata_tiff] * 3)
    ref = np.array([0.1, 0.1, 0.1])
    np.testing.assert_array_almost_equal(rst, ref)


@pytest.fixture(scope="module")
def tiff_with_metadata(tmpdir_factory):
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
    return ct, ob, dc, ct_alt


def test_get_filelist_by_dir(tiff_with_metadata):
    ct, ob, dc, ct_alt = list(map(str, tiff_with_metadata))
    ct_dir = Path(ct).parent
    ob_dir = Path(ob).parent
    dc_dir = Path(dc).parent
    ct_alt_dir = Path(ct_alt).parent
    # error_0: ct_dir does not exists
    with pytest.raises(ValueError):
        _get_filelist_by_dir(ct_dir="dummy", ob_dir="/tmp", dc_dir="/tmp")
    # error_1: ob_dir does not exists
    with pytest.raises(ValueError):
        _get_filelist_by_dir(ct_dir="/tmp", ob_dir="dummy", dc_dir="/tmp")
    # case_0: load all three
    rst = _get_filelist_by_dir(
        ct_dir=ct_dir,
        ob_dir=ob_dir,
        dc_dir=dc_dir,
        ct_fnmatch="*.tiff",
        ob_fnmatch="*.tiff",
        dc_fnmatch="*.tiff",
    )
    assert rst == ([ct], [ob], [dc])
    # case_1: load ct and ob, skipping dc
    rst = _get_filelist_by_dir(
        ct_dir=ct_dir,
        ob_dir=ob_dir,
        ct_fnmatch="*.tiff",
        ob_fnmatch="*.tiff",
        dc_fnmatch="*.tiff",
    )
    assert rst == ([ct], [ob], [])
    # case_2: load ct, and detect ob and dc from metadata
    rst = _get_filelist_by_dir(
        ct_dir=ct_dir,
        ob_dir=ob_dir,
        dc_dir=dc_dir,
        ct_fnmatch="*.tiff",
        ob_fnmatch=None,
        dc_fnmatch=None,
    )
    assert rst == ([ct], [ob], [dc])
    # case_3: load ct, and detect ob from metadata
    rst = _get_filelist_by_dir(
        ct_dir=ct_dir,
        ob_dir=ob_dir,
        ct_fnmatch="*.tiff",
        ob_fnmatch=None,
    )
    assert rst == ([ct], [ob], [])
    # case_4: load ct_alt, and find no match ob
    rst = _get_filelist_by_dir(
        ct_dir=ct_alt_dir,
        ob_dir=ob_dir,
        ct_fnmatch="*.tiff",
        ob_fnmatch=None,
    )
    assert rst == ([ct_alt], [], [])
    # case_5: did not find any match for ct
    rst = _get_filelist_by_dir(
        ct_dir=ct_dir,
        ob_dir=ob_dir,
        ct_fnmatch="*.not_exist",
        ob_fnmatch=None,
    )
    assert rst == ([], [], [])


def test_save_data_fail():
    with pytest.raises(ValueError):
        save_data()


def check_savefiles(direc: Path, prefix: str, num_files: int = 3, has_omega=False):
    assert direc.exists()
    assert direc.is_dir()
    filepaths = [direc / item for item in direc.iterdir()]
    assert len(filepaths) == num_files
    for filepath in filepaths:
        print(filepath)
        assert filepath.is_file()
        if has_omega and filepath.name == "rot_angles.npy":
            continue
        assert filepath.suffix == ".tiff"
        # the names are zero-padded
        assert "_0000" in filepath.name
        # verify the file starts with the name
        assert filepath.name.startswith(prefix)


def create_fake_data():
    return np.zeros((3, 3, 3)) + 1.0


@pytest.mark.parametrize("name", ["junk", ""])  # gets default name
def test_save_data(name):
    data = create_fake_data()
    omegas = np.asarray([1.0, 2.0, 3.0])
    # this context will remove directory on exit
    with TemporaryDirectory() as tmpdirname:
        assert tmpdirname
        tmpdir = Path(tmpdirname)

        # run the code
        numfiles = 3
        if name:
            outputdir = save_data(data=data, outputbase=tmpdir, name=name, rot_angles=omegas)
            numfiles += 1
        else:
            outputdir = save_data(data=data, outputbase=tmpdir)
        print(outputdir)

        # check the result
        if name:
            prefix = name + "_"
        else:
            prefix = "save_data_"  # special name

        assert outputdir.name.startswith(prefix), str(outputdir.name)
        check_savefiles(outputdir, prefix, has_omega=bool(name), num_files=numfiles)


def test_save_data_subdir():
    name = "subdirtest"
    # this context will remove directory on exit
    with TemporaryDirectory() as tmpdirname:
        data = create_fake_data()
        tmpdir = Path(tmpdirname) / "subdirectory"  # make it create a subdirectory

        # run the code
        outputdir = save_data(data=data, outputbase=tmpdir, name=name)
        assert outputdir.name.startswith(f"{name}_"), str(outputdir)

        # check the result
        check_savefiles(outputdir, "subdirtest_")


def test_save_checkpoint():
    name = "chktest"
    data = create_fake_data()

    # check without omegas
    with TemporaryDirectory() as tmpdirname:
        assert tmpdirname
        omegas = np.asarray([1.0, 2.0, 3.0])
        tmpdir = Path(tmpdirname)

        outputdir = save_checkpoint(data=data, outputbase=tmpdir, name=name)

        assert outputdir.name.startswith(f"{name}_chkpt_"), str(outputdir)
        # check the tiffs result
        check_savefiles(outputdir, "chk", num_files=3)

    # check with omegas
    with TemporaryDirectory() as tmpdirname:
        assert tmpdirname
        omegas = np.asarray([1.0, 2.0, 3.0])
        tmpdir = Path(tmpdirname)

        outputdir = save_checkpoint(data=data, outputbase=tmpdir, name=name, rot_angles=omegas)

        assert outputdir.name.startswith(f"{name}_chkpt_"), str(outputdir)
        # check the tiffs result
        check_savefiles(outputdir, "chk", num_files=4, has_omega=True)


if __name__ == "__main__":
    pytest.main([__file__])
