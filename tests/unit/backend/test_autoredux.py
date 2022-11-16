#!/usr/bin/env python3

# package imports
from imars3d.backend import auto_reduction_ready
from imars3d.backend import load_template_config
from imars3d.backend import extract_info_from_path
from imars3d.backend import substitute_template

# third party imports
import pytest

# standard imports
from pathlib import Path


@pytest.mark.parametrize(
    "path_to_file, value",
    [
        ("/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/some.tiff", True),
        ("/HFIR/CG1D/IPTS-25777/raw/df/iron_man/some.tiff", False),
        ("/HFIR/CG1D/IPTS-25777/raw/ob/iron_man/some.tiff", False),
        ("/HFIR/CG1D/IPTS-25777/ct_scans/iron_man/some.tiff", False),
    ],
)
def test_auto_reduction_ready(path_to_file, value):
    assert auto_reduction_ready(path_to_file) is value


def test_load_template_config():
    # NOTE: update the test when template json is created
    with pytest.raises(FileNotFoundError):
        _ = load_template_config("")


@pytest.mark.parametrize(
    "data_file, prepath, subpath",
    [
        ("/HFIR/CG1D/IPTS-25777/raw/ct_scans/", "", ""),
        ("/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/", "", "iron_man"),
        ("/HFIR/CG1D/IPTS-25777/raw/2022-nov/11/ct_scans/iron_man/x", "2022-nov/11", "iron_man/x"),
    ],
)
def test_extract_from_path(data_file, prepath, subpath):
    path = Path(data_file) / "some.tiff"
    data = extract_info_from_path(path)
    assert data["facility"] == "HFIR"
    assert data["instrument"] == "CG1D"
    assert data["ipts"] == "IPTS-25777"
    assert data["prepath"] == prepath
    assert data["subpath"] == subpath


def test_extract_bad_path():
    path = "HFIR/CG1D/IPTS-25777/raw/ct_scans/some.tiff"
    with pytest.raises(AssertionError) as e:
        extract_info_from_path(path)
    assert str(e.value) == "Path HFIR/CG1D/IPTS-25777/raw/ct_scans/some.tiff is not an absolute path"
    path = "/HFIR/CG1D/IPTS-25777/raw/yadayada/some.tiff"
    with pytest.raises(AssertionError) as e:
        extract_info_from_path(path)
    assert str(e.value) == "No radiographs directory found"

def test_substitute_template():
    # load config template
    config_path = Path(__file__).parents[3] / "scripts/reduce_CG1D_config_template.json"
    config_dict = load_template_config(config_path)
    update_dict = extract_info_from_path("/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/some.tiff")
    update_dict["outputdir"] = "outputdir"
    update_dict["workingdir"] = "workingdir"
    assert config_dict["facility"] == "$facility"
    assert config_dict["instrument"] == "$instrument"
    assert config_dict["ipts"] == "$ipts"
    assert config_dict["name"] == "reduce_$instrument"
    assert config_dict["workingdir"] == "$workingdir"
    assert config_dict["outputdir"] == "$outputdir"
    config_dict = substitute_template(config_dict, update_dict)
    assert config_dict["facility"] == "HFIR"
    assert config_dict["instrument"] == "CG1D"
    assert config_dict["ipts"] == "IPTS-25777"
    assert config_dict["name"] == "reduce_CG1D"
    assert config_dict["workingdir"] != "$workingdir"
    assert config_dict["outputdir"] != "$outputdir"

def test_substitute_template_bad_values():
    # load config template
    config_path = Path(__file__).parents[3] / "scripts/reduce_CG1D_config_template.json"
    config_dict = load_template_config(config_path)
    update_dict = extract_info_from_path("/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/some.tiff")
    # Leaving outputdir and workingdir empty to cause a KeyError
    with pytest.raises(KeyError):
        _ = substitute_template(config_dict, update_dict)

if __name__ == "__main__":
    pytest.main([__file__])
