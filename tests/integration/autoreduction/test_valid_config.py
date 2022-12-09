# package imports
from imars3d.backend.autoredux import extract_info_from_path, substitute_template
from imars3d.backend.dataio.data import _load_images as load_images
from imars3d.backend.util.functions import clamp_max_workers
from reduce_CG1D import main as main_CG1D
from reduce_CG1D import WORKFLOW_SUCCESS

# third-party imports
import numpy as np
import pytest

# standard imports
import os
from pathlib import Path
from psutil import virtual_memory
import re
from unittest import mock
from unittest.mock import MagicMock


@pytest.fixture(scope="module")
def tweak_extract_info_from_path():
    r"""Call extract_info after amending the input_tiff Path
    The amended path should start as /HFIR/CG1D/ so that
    extract_info_from_path() can work properly
    """

    def _tweak_extract_info_from_path(path_to_tiff: Path) -> dict:
        items = Path(path_to_tiff).parts
        new_path = Path("/" + os.path.sep.join(items[items.index("HFIR") :]))
        config = extract_info_from_path(new_path)
        return config

    return _tweak_extract_info_from_path


@pytest.fixture(scope="module")
def tweak_substitute_template(DATA_DIR):
    r"""Amend the path to the data directories because they don't conform to the convention"""

    def _tweak_substitute_template(config: dict, values: dict) -> dict:
        updated = substitute_template(config, values)
        assert updated["tasks"][0]["name"] == "load_data"
        inputs = updated["tasks"][0]["inputs"]
        path_to_raw = Path(inputs["ct_dir"]).parent.parent  # /HFIR/CG1D/IPTS-25777/raw
        path_to_raw = path_to_raw.relative_to(DATA_DIR.anchor)  # transform to a relative path
        inputs["ct_dir"] = str(DATA_DIR / path_to_raw / "ct_scans/iron_man")
        inputs["ob_dir"] = str(DATA_DIR / path_to_raw / "ob/Oct29_2019")  # suffix should also be "iron_man"
        inputs["dc_dir"] = str(DATA_DIR / path_to_raw / "df/Oct29_2019")
        return updated

    return _tweak_substitute_template


@pytest.mark.datarepo
@mock.patch("reduce_CG1D.substitute_template")
@mock.patch("reduce_CG1D.extract_info_from_path")
def test_valid_config(
    mock_extract_info_from_path: MagicMock,
    mock_substitute_template: MagicMock,
    tweak_extract_info_from_path,
    tweak_substitute_template,
    DATA_DIR: Path,
    JSON_DIR: Path,
    IRON_MAN_DIR: Path,
    tmpdir: Path,
    caplog,
):
    MEM_AVAILABLE = int(virtual_memory().available / 1024 / 1024 / 1024)
    MEM_REQUIRED = 23
    if MEM_AVAILABLE < MEM_REQUIRED:
        msg = f"Insufficient memory to run the test: found {MEM_AVAILABLE}GiB require {MEM_REQUIRED}GiB"
        pytest.fail(msg)
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    mock_extract_info_from_path.return_value = tweak_extract_info_from_path(last_tiff)
    mock_substitute_template.side_effect = tweak_substitute_template
    # Check for autoreduction success
    assert main_CG1D(last_tiff, tmpdir) == WORKFLOW_SUCCESS

    # Check log messages
    for filter_name in [
        "Crop",
        "Gamma Filter",
        "Normalization",
        "Remove Ring Artifact",
        "Find Rotation Center",
        "Reconstruction",
    ]:
        assert f"FINISHED Executing Filter: {filter_name}" in caplog.text

    # Check for saved configuration
    config_path = re.search(r"Configuration saved to ([-/\.\w]+)\n", caplog.text).groups()[0]
    assert Path(config_path).exists()

    # Check resulting radiographs by extracting a slice and cropping to region of interest
    radiographs_dir = re.search(r'saving tiffs to "([-/\.\w]+)"', caplog.text).groups()[0]
    assert Path(radiographs_dir).exists()
    output_tiffs = sorted([str(file) for file in Path(radiographs_dir).glob("*.tiff")])
    assert len(output_tiffs) == 525, f"{config_path} should have 525 tiffs"

    result = load_images(filelist=output_tiffs, desc="test", max_workers=clamp_max_workers(None), tqdm_class=None)
    slice_cropped = result[42, 400:600, 400:600]
    expected = np.load(str(DATA_DIR.parent / "integration" / "backend" / "expected_slice_42.npy"))
    np.testing.assert_allclose(slice_cropped, expected, atol=1.0e-6)


if __name__ == "__main__":
    pytest.main([__file__])
