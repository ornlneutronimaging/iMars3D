# standard imports
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
import gc
from unittest.mock import patch

import pytest


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


def sequential_process_map(fn, *iterables, **kwargs):
    """Sequential replacement for process_map to avoid multiprocessing issues in tests."""
    # Extract relevant kwargs
    tqdm_class = kwargs.pop("tqdm_class", None)
    desc = kwargs.pop("desc", None)
    total = kwargs.pop("total", len(iterables[0]) if iterables else 0)
    
    # Use tqdm if provided
    if tqdm_class:
        from tqdm import tqdm
        results = []
        for items in tqdm(zip(*iterables), total=total, desc=desc):
            results.append(fn(*items))
        return results
    else:
        # Simple sequential map
        return list(map(fn, *iterables))


@pytest.fixture(autouse=True)
def patch_process_map():
    """Replace process_map with sequential version in tests to avoid hanging."""
    # Patch at multiple locations where it's imported
    patches = [
        patch('tqdm.contrib.concurrent.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.diagnostics.rotation.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.diagnostics.tilt.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.corrections.intensity_fluctuation_correction.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.corrections.beam_hardening.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.corrections.denoise.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.corrections.ring_removal.process_map', side_effect=sequential_process_map),
        patch('imars3d.backend.dataio.data.process_map', side_effect=sequential_process_map),
    ]
    
    for p in patches:
        p.start()
    
    yield
    
    for p in patches:
        p.stop()
    
    # Force garbage collection after test
    gc.collect()
