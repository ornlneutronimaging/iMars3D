from imars3d.backend.__main__ import main
from pathlib import Path
import pytest
from json.decoder import JSONDecodeError


def test_bad(JSON_DIR):
    bad_json = JSON_DIR / "ill_formed.json"
    with pytest.raises(JSONDecodeError):
        main([str(bad_json)])


def test_good(JSON_DIR):
    good_json = JSON_DIR / "good_interactive.json"

    main([str(good_json)])


if __name__ == "__main__":
    pytest.main([__file__])
