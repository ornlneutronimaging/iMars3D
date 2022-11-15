# package imports
from reduce_CG1D import main as main_CG1D
from reduce_CG1D import WORKFLOW_SUCCESS

# third-party imports
import pytest

# standard imports
import json
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock


@pytest.fixture(scope="module")
def load_template(IRON_MAN_DIR):
    r"""Load the template and set paths for radiographs, open-beam, and dark-current"""

    def _load_template(config_path: Path):
        with open(config_path, "r") as template_config:
            config = json.load(template_config)
        # replace relative with absolute paths
        inputs = config["tasks"][0]["inputs"]
        inputs["ct_dir"] = str(IRON_MAN_DIR)
        inputs["ob_dir"] = str(IRON_MAN_DIR.parent.parent / "ob" / "Oct29_2019")
        inputs["dc_dir"] = str(IRON_MAN_DIR.parent.parent / "df" / "Oct29_2019")
        return config

    return _load_template


# TODO: remove the mocks as the parts of reduce_CG1D become completed
@mock.patch("reduce_CG1D.extract_info_from_path")
@mock.patch("reduce_CG1D.load_template_config")
@mock.patch("reduce_CG1D._find_template_config")
def test_valid_config(
    mock__find_template_config: MagicMock,
    mock_load_template_config: MagicMock,
    mock_extract_info_from_path: MagicMock,
    load_template,
    JSON_DIR: Path,
    IRON_MAN_DIR: Path,
    tmp_path: Path,
    caplog,
):
    mock__find_template_config.return_value = JSON_DIR / "good_non_interactive_full.json"
    mock_load_template_config.return_value = load_template(JSON_DIR / "good_non_interactive_full.json")
    mock_extract_info_from_path.return_value = {
        "ipts": "IPTS-25777",
        "name": "reduce CG1D",
        "workingdir": str(tmp_path),
        "outputdir": str(tmp_path),
    }
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    assert main_CG1D(last_tiff, tmp_path) == WORKFLOW_SUCCESS
    assert "" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__])
