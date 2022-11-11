# package imports
from reduce_CG1D import ERROR_GENERAL
from reduce_CG1D import main as main_CG1D

# third-party imports
import pytest

# standard imports
from pathlib import Path


@pytest.mark.datarepo
def test_no_template(IRON_MAN_DIR: Path, tmp_path: Path):
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    exit_code = main_CG1D(last_tiff, tmp_path)
    assert exit_code == ERROR_GENERAL
    # fetch string in the logs


if __name__ == "__main__":
    pytest.main([__file__])
