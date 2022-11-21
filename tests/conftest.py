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


@pytest.fixture(scope="module")
def cleanfile():
    """Fixture that deletes registered files when the .py file is finished. It
    will cleanup on exception and will safely skip over files that do not
    exist. Do not use this if you want the files to remain for a failing test.

    Usage:

    def test_something(cleanfile):
        cleanfile('/some/file/the/test.creates')
        # do stuff
    """
    filenames = []

    def _cleanfile(filename):
        filenames.append(Path(filename))
        return filename

    yield _cleanfile

    for filename in filenames:
        if filename.exists():
            if filename.is_dir():
                rmtree(filename)  # remove the directory and any files that are in it
            else:
                filename.unlink()  # remove the single file


# NOTE: pytest fixtures tmp_path and tmp_path_factory are NOT deleting the temporary directory, hence this fixture
@pytest.fixture(scope="function")
def tmpdir():
    r"""Create directory, then delete the directory and its contents upon test exit"""
    try:
        temporary_dir = Path(mkdtemp())
        yield temporary_dir
    finally:
        rmtree(temporary_dir)
