import json
from json import JSONDecodeError
from jsonschema.exceptions import ValidationError
import pytest
from pathlib import Path
from imars3d.backend.workflow.validate import JSONValid, JSONValidationError

JSON_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "json"
GOOD_FILE = JSON_DATA_DIR / "good.json"
ILL_FORMED_FILE = JSON_DATA_DIR / "ill_formed.json"


class MockContainer:
    """Mock class for mimicing how json validation will work in practice"""

    config = JSONValid()

    def __init__(self, obj):
        self.config = obj


def load_file(filepath: Path) -> str:
    """Utility function for loading json from file"""

    with open(filepath, "r") as handle:
        data = handle.read()
    return data


# tests from file


def test_file_not_exist():
    with pytest.raises(FileNotFoundError):
        MockContainer(Path("non-existant-file"))


def test_file_ill_formed():
    print("Testing file", ILL_FORMED_FILE)
    with pytest.raises(JSONDecodeError):
        MockContainer(ILL_FORMED_FILE)


def test_file_good():
    print("Testing file", GOOD_FILE)
    MockContainer(GOOD_FILE)


# tests from string


def test_string_empty():
    with pytest.raises(JSONDecodeError):
        MockContainer("")


def test_string_ill_formed():
    doc = load_file(ILL_FORMED_FILE)
    with pytest.raises(JSONDecodeError):
        MockContainer(doc)


def test_string_good():
    doc = load_file(GOOD_FILE)
    obj = MockContainer(doc)
    # verify that the instrument is as expected
    assert obj._json["instrument"] == "cg1d"


def test_string_missing_tasks():
    doc = load_file(GOOD_FILE)
    json_obj = json.loads(doc)
    del json_obj["tasks"]
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


def test_string_empty_function():
    doc = load_file(GOOD_FILE)
    json_obj = json.loads(doc)
    json_obj["tasks"][0]["function"] = ""
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


def test_string_bad_function():
    doc = load_file(GOOD_FILE)
    json_obj = json.loads(doc)
    json_obj["tasks"][0]["function"] = "nonexistent.function"
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))

    json_obj["tasks"][0]["function"] = "toplevelfunction"
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


if __name__ == "__main__":
    pytest.main([__file__])
