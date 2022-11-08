from imars3d.backend.__main__ import main as main_backend
from reduce_CG1D import main as main_CG1D
from pathlib import Path
import pytest
from json.decoder import JSONDecodeError

TIFF_DIR = "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man"

class TestCLIAutoreduction:
    outputdir = "/tmp/imars3d/"

    def test_outputfir_not_writable(self):
        assert main_CG1D(TIFF_DIR, "this/dir/doesnt/exist") != 0

if __name__ == "__main__":
    pytest.main([__file__])

