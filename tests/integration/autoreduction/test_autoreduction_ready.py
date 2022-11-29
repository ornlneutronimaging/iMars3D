# package imports
from reduce_CG1D import main as main_CG1D
from reduce_CG1D import ERROR_GENERAL, SCAN_INCOMPLETE

# third-party imports
import pytest

# standard imports
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock


@pytest.mark.datarepo
@mock.patch("reduce_CG1D._find_template_config")
def test_auto_reduction_ready(mock__find_template_config: MagicMock, caplog, IRON_MAN_DIR: Path, tmp_path: Path):
    # Force _find_template_config() to throw error in order to stop execution of main_CG1D()
    # right after auto_reduction_ready() is called
    mock__find_template_config.side_effect = FileNotFoundError("Mocked _find_template_config raises")
    raw_dir = IRON_MAN_DIR.parent.parent

    # non-canonical data file path
    bad_path_tiff = tmp_path / "20191030_OB_0070_0625.tiff"
    open(bad_path_tiff, "w").write("")
    assert main_CG1D(bad_path_tiff, tmp_path) == SCAN_INCOMPLETE
    assert "non-canonical data file path" in caplog.text

    # checking an open beam
    caplog.clear()
    ob_tiff = raw_dir / "ob" / "Oct29_2019" / "20191030_OB_0070_0625.tiff"
    assert main_CG1D(ob_tiff, tmp_path) == SCAN_INCOMPLETE
    assert "The input image is not a radiograph." in caplog.text

    # checking a dark field
    caplog.clear()
    df_tiff = raw_dir / "df" / "Oct29_2019" / "20191030_DF_0070_0632.tiff"
    assert main_CG1D(df_tiff, tmp_path) == SCAN_INCOMPLETE
    assert "The input image is not a radiograph." in caplog.text

    # TODO: the first_tiff should return a non-complete scan
    caplog.clear()
    first_tiff = IRON_MAN_DIR / "20191029_ironman_small_0070_000_000_0002.tiff"
    assert main_CG1D(first_tiff, tmp_path) == ERROR_GENERAL
    assert "Mocked _find_template_config raises" in caplog.text
    assert "Scan is complete." in caplog.text  # should be "Scan is not complete."

    # TODO: last_tiff should return a complete scan but we're not picking the complete-scan signal
    caplog.clear()
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    assert main_CG1D(last_tiff, tmp_path) == ERROR_GENERAL
    assert "Scan is complete." in caplog.text


if __name__ == "__main__":
    pytest.main([__file__])
