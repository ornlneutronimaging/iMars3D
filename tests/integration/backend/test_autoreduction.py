from imars3d.backend.__main__ import main as main_backend
from reduce_CG1D import main as main_CG1D
from pathlib import Path
import pytest
from json.decoder import JSONDecodeError
import os

TIFF_DIR = "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man"


class TestCLIAutoreduction:
    outputdir = "/tmp/imars3d/"

    @pytest.fixture(autouse=True)
    def buildup_teardown(self, tmpdir):
        """Fixture to execute asserts before and after a test is run"""
        # Setup: fill with any logic you want
        shutil.rmtree(path=self.outputdir, ignore_errors=True)
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        yield  # this is where the testing happens
        shutil.rmtree(path=self.outputdir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])
