from imars3d.backend.__main__ import main as main_backend
from reduce_CG1D import main as main_CG1D
from pathlib import Path
import pytest
from json.decoder import JSONDecodeError


def test_bad(JSON_DIR):
    bad_json = JSON_DIR / "ill_formed.json"
    with pytest.raises(JSONDecodeError):
        main_backend([str(bad_json)])


def test_good(JSON_DIR):
    good_json = JSON_DIR / "good_interactive.json"

    main_backend([str(good_json)])


def test_CG1D_autoreduction():
    assert main_CG1D("bad", "also bad") != 0


if __name__ == "__main__":
    pytest.main([__file__])
