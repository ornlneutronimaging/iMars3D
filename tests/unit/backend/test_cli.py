from imars3d.backend.__main__ import main as main_backend
from reduce_CG1D import main as main_CG1D
import pytest
from json.decoder import JSONDecodeError


@pytest.fixture(scope="module")
def TIFF_RANDOM(IRON_MAN_DIR):
    return IRON_MAN_DIR / "20191030_ironman_small_0070_233_740_0405.tiff"


def test_bad(JSON_DIR):
    bad_json = JSON_DIR / "ill_formed.json"
    with pytest.raises(JSONDecodeError):
        main_backend([str(bad_json)])


def test_good(JSON_DIR):
    good_json = JSON_DIR / "good_interactive.json"

    main_backend([str(good_json)])


@pytest.mark.datarepo
def test_outputdir_not_writable(TIFF_RANDOM):
    assert main_CG1D(TIFF_RANDOM, "this/dir/doesnt/exist") == 1


def test_input_dir_doesnt_exist():
    assert main_CG1D("this/dir/doesnt/exist", "/tmp/") == 1


if __name__ == "__main__":
    pytest.main([__file__])
