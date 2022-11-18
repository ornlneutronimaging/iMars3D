from imars3d.backend.__main__ import main as main_backend
from reduce_CG1D import main as main_CG1D
from reduce_CG1D import ERROR_GENERAL
import pytest
from json.decoder import JSONDecodeError

TIFF_DIR = "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man"


def test_bad(JSON_DIR):
    bad_json = JSON_DIR / "ill_formed.json"
    with pytest.raises(JSONDecodeError):
        main_backend([str(bad_json)])


def test_good(JSON_DIR):
    good_json = JSON_DIR / "good_interactive.json"

    main_backend([str(good_json)])


@pytest.mark.datarepo
def test_outputdir_not_writable():
    assert main_CG1D(TIFF_DIR, "this/dir/doesnt/exist") == ERROR_GENERAL


def test_input_dir_doesnt_exist():
    assert main_CG1D("this/dir/doesnt/exist", "/tmp/") == ERROR_GENERAL


if __name__ == "__main__":
    pytest.main([__file__])
