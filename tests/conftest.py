# standard imports
import logging
from io import StringIO
from pathlib import Path
import pytest
from shutil import rmtree


@pytest.fixture(scope="session")
def string_handler():
    r"""Direct the logs to a string stream
    Parameters
    ----------
    logger : logging.Logger
        the logger to which the string streams attaches itself
    level : int
        logging level, default is logging.DEBUG
    """

    class StringStreamHandler(StringIO):
        def __init__(self, logger: logging.Logger, level: int = logging.DEBUG):
            super().__init__()
            self.handler = logging.StreamHandler(stream=self)
            self.handler.setLevel(level)

            logger.addHandler(self.handler)

        def __str__(self) -> str:
            return self.getvalue()

        def clear(self):
            r"""Delete the logged contents"""
            self.truncate(0)
            self.seek(0)

    return StringStreamHandler


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
