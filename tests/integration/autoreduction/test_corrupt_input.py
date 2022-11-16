# package imports
from reduce_CG1D import ERROR_GENERAL
from reduce_CG1D import main as main_CG1D
from imars3d.backend.workflow.validate import JSONValidationError

# third-party imports
import pytest

# standard imports
from json import JSONDecodeError
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock


@pytest.mark.datarepo
@mock.patch("reduce_CG1D._find_template_config")
def test_corrupt_template_malformed_json(mock__find_template_config: MagicMock, caplog, IRON_MAN_DIR: Path, tmp_path: Path):
    corrupt_template = "reduce_config_template_malformed.json"
    # malformed json file is in tests/data/json
    test_data_dir = Path(__file__).parents[2] / "data/json"
    path_to_file = test_data_dir / corrupt_template
    mock__find_template_config.return_value = path_to_file
    test_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    with pytest.raises(JSONDecodeError):
        _ = main_CG1D(test_tiff, tmp_path)

@pytest.mark.datarepo
@mock.patch("reduce_CG1D._find_template_config")
def test_corrupt_template_wrong_key(mock__find_template_config: MagicMock, caplog, IRON_MAN_DIR: Path, tmp_path: Path):
    corrupt_template = "reduce_config_template_corrupt.json"
    # corrupt json file is in tests/data/json
    test_data_dir = Path(__file__).parents[2] / "data/json"
    path_to_file = test_data_dir / corrupt_template
    mock__find_template_config.return_value = path_to_file
    test_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    with pytest.raises(JSONValidationError):
        _ = main_CG1D(test_tiff, tmp_path)
 

if __name__ == "__main__":
    pytest.main([__file__])

