# package imports
from reduce_CG1D import main as main_CG1D

# third-party imports
import pytest

# standard imports
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock


@pytest.mark.datarepo
@mock.patch("reduce_CG1D._find_template_config")
@mock.patch("imars3d.backend.extract_info_from_path")
def test_corrupt_template(
    mock_extract_info_from_path: MagicMock,
    mock__find_template_config: MagicMock,
    caplog,
    IRON_MAN_DIR: Path,
    tmp_path: Path,
):
    corrupt_template = "reduce_config_template_corrupt.json"
    # corrupt json file is in tests/data/json
    test_data_dir = Path(__file__).parents[2] / "data/json"
    path_to_file = test_data_dir / corrupt_template
    mock__find_template_config.return_value = path_to_file
    mock_update_dict = {"facility": "HFIR", "instrument": "CG1D", "ipts": "IPTS-25777", "prepath": "/", "subpath": "/"}
    mock_extract_info_from_path.return_value = mock_update_dict
    test_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    error_code = main_CG1D(test_tiff, tmp_path)
    assert error_code != 0
    assert "Config template dict is missing keys." in caplog.text


if __name__ == "__main__":
    pytest.main([__file__])
