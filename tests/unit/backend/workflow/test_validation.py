from json import JSONDecodeError
import pytest
from pathlib import Path
from imars3d.backend.workflow.validate import validate, validates

JSON_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "json"
GOOD_FILE = JSON_DATA_DIR / "good.json"
ILL_FORMED_FILE = JSON_DATA_DIR / "ill_formed.json"

# tests from file


def test_file_not_exist():
    with pytest.raises(FileNotFoundError):
        validate("non-existant-file")


def test_file_ill_formed():
    print("Testing file", ILL_FORMED_FILE)

    with pytest.raises(JSONDecodeError):
        validate(ILL_FORMED_FILE)


def test_file_good():
    print("Testing file", GOOD_FILE)
    validate(GOOD_FILE)


# tests from string


def load_file(filepath: Path) -> str:
    with open(filepath, "r") as handle:
        data = handle.read()
    return data


def test_string_empty():
    with pytest.raises(JSONDecodeError):
        validates("")


def test_string_ill_formed():
    doc = load_file(ILL_FORMED_FILE)
    with pytest.raises(JSONDecodeError):
        validates(doc)


def test_string_good():
    doc = load_file(GOOD_FILE)
    validates(doc)


if __name__ == "__main__":
    pytest.main([__file__])
