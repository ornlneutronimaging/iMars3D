# package imports
from reduce_CG1D import main as main_CG1D
from reduce_CG1D import ERROR_GENERAL
from imars3d.backend.autoredux import logger

# third-party imports
import pytest

# standard imports
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock


@pytest.mark.datarepo
@mock.patch("reduce_CG1D._find_template_config")
def test_auto_reduction_ready(
    mock__find_template_config: MagicMock, string_handler, IRON_MAN_DIR: Path, tmp_path: Path
):
    # Force _find_template_config() to throw error in order to stop execution of main_CG1D()
    # right after auto_reduction_ready() is called
    mock__find_template_config.side_effect = FileNotFoundError("Mocked _find_template_config raises")
    streamer = string_handler(logger)  # capture the auto-reduction logger to a string
    raw_dir = IRON_MAN_DIR.parent.parent

    # non-canonical data file path
    bad_path_tiff = tmp_path / "20191030_OB_0070_0625.tiff"
    open(bad_path_tiff, "w").write("")
    assert main_CG1D(bad_path_tiff, tmp_path) == ERROR_GENERAL
    assert "non-canonical data file path" in str(streamer)

    # checking an open beam
    streamer.clear()  # delete the contents logged up to this point
    ob_tiff = raw_dir / "ob" / "Oct29_2019" / "20191030_OB_0070_0625.tiff"
    assert main_CG1D(ob_tiff, tmp_path) == ERROR_GENERAL
    assert "The input image is not a radiograph." in str(streamer)

    # checking a dark field
    streamer.clear()
    df_tiff = raw_dir / "df" / "Oct29_2019" / "20191030_DF_0070_0632.tiff"
    assert main_CG1D(df_tiff, tmp_path) == ERROR_GENERAL
    assert "The input image is not a radiograph." in str(streamer)

    # TODO: the first_tiff should return a non-complete scan
    streamer.clear()
    first_tiff = IRON_MAN_DIR / "20191029_ironman_small_0070_000_000_0002.tiff"
    assert main_CG1D(first_tiff, tmp_path) == ERROR_GENERAL
    assert "Mocked _find_template_config raises" in str(streamer)
    assert "Scan is complete." in str(streamer)  # should be "Scan is not complete."

    # TODO: last_tiff should return a complete scan but we're not picking the complete-scan signal
    streamer.clear()
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    assert main_CG1D(last_tiff, tmp_path) == ERROR_GENERAL
    assert "Mocked _find_template_config raises" in str(streamer)
    assert "Scan is complete." in str(streamer)


if __name__ == "__main__":
    pytest.main([__file__])
