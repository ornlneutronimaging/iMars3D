# standard imports
from pathlib import Path
import pytest
from shutil import rmtree
from tempfile import mkdtemp


@pytest.fixture(scope="session")
def JSON_DIR():
    return Path(__file__).parent / "data" / "json"


@pytest.fixture(scope="session")
def DATA_DIR():
    return Path(__file__).parent / "data" / "imars3d-data"


@pytest.fixture(scope="session")
def IRON_MAN_DIR(DATA_DIR):
    return DATA_DIR / "HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man"


# NOTE: pytest fixtures tmp_path and tmp_path_factory are NOT deleting the temporary directory, hence this fixture
@pytest.fixture(scope="function")
def tmpdir():
    r"""Create directory, then delete the directory and its contents upon test exit"""
    try:
        temporary_dir = Path(mkdtemp())
        yield temporary_dir
    finally:
        rmtree(temporary_dir)
