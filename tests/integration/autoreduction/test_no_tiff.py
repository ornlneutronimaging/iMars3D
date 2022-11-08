# package imports
from reduce_CG1D import main as main_CG1D

# third-party imports
import pytest


@pytest.mark.datarepo
def test_no_tiff(IRON_MAN_DIR, tmp_path):
    # Check for CG1D
    no_tiff = IRON_MAN_DIR / "20191042_ironman_small_0070_360_760_0624.tiff"
    exit_code = main_CG1D(str(no_tiff), str(tmp_path))
    assert exit_code == 1


if __name__ == "__main__":
    pytest.main([__file__])
