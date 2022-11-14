# package imports
import logging

from reduce_CG1D import ERROR_GENERAL, logger
from reduce_CG1D import main as main_CG1D

# third-party imports
import pytest

# standard imports
from pathlib import Path


@pytest.mark.datarepo
def test_no_template(IRON_MAN_DIR: Path, tmp_path: Path, caplog):
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    assert main_CG1D(last_tiff, tmp_path) == ERROR_GENERAL
    assert "Template reduce_CG1D_config_template.json not found" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__])
