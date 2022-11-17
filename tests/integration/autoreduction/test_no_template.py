# package imports
from reduce_CG1D import main as main_CG1D
from reduce_CG1D import ERROR_GENERAL

# third-party imports
import pytest

# standard imports
import os
from pathlib import Path


@pytest.fixture(autouse=True)
def setup_rename_template():
    template_path = Path(__file__).parents[3] / "scripts/reduce_CG1D_config_template.json"
    os.rename(template_path, template_path.with_stem("temp_rename"))
    yield
    os.rename(template_path.with_stem("temp_rename"), template_path)


@pytest.mark.datarepo
def test_no_template(IRON_MAN_DIR: Path, tmp_path: Path, caplog):
    last_tiff = IRON_MAN_DIR / "20191030_ironman_small_0070_360_760_0624.tiff"
    assert main_CG1D(last_tiff, tmp_path) == ERROR_GENERAL
    assert "Template reduce_CG1D_config_template.json not found" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__])
