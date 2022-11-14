import json
from json import JSONDecodeError
import pytest
from pathlib import Path
from imars3d.backend.workflow.validate import JSONValid, JSONValidationError, SCHEMA


# fixtures here re-use the JSON_DIR fixture defined in conftest.py
@pytest.fixture(scope="module")
def GOOD_NON_INTERACTIVE(JSON_DIR):
    return JSON_DIR / "good_non_interactive.json"


@pytest.fixture(scope="module")
def GOOD_INTERACTIVE(JSON_DIR):
    return JSON_DIR / "good_interactive.json"


@pytest.fixture(scope="module")
def GOOD_INTERACTIVE_FULL(JSON_DIR):
    return JSON_DIR / "good_non_interactive_full.json"


@pytest.fixture(scope="module")
def ILL_FORMED_FILE(JSON_DIR):
    return JSON_DIR / "ill_formed.json"


class MockContainer:
    """Mock class for mimicking how json validation will work in practice"""

    config = JSONValid()

    def __init__(self, obj):
        self.schema = SCHEMA
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


def test_file_ill_formed(ILL_FORMED_FILE):
    print("Testing file", ILL_FORMED_FILE)
    with pytest.raises(JSONDecodeError):
        MockContainer(ILL_FORMED_FILE)


@pytest.mark.parametrize("filename", ["GOOD_NON_INTERACTIVE", "GOOD_INTERACTIVE_FULL", "GOOD_INTERACTIVE"])
def test_file_good(filename, request):
    fileobj = request.getfixturevalue(filename)
    print("Testing file", fileobj)
    MockContainer(fileobj)


# tests from string


def test_string_empty():
    with pytest.raises(JSONDecodeError):
        MockContainer("")


def test_string_ill_formed(ILL_FORMED_FILE):
    doc = load_file(ILL_FORMED_FILE)
    with pytest.raises(JSONDecodeError):
        MockContainer(doc)


def test_string_good(GOOD_NON_INTERACTIVE):
    doc = load_file(GOOD_NON_INTERACTIVE)
    obj = MockContainer(doc)
    # verify that the instrument is as expected
    assert obj._json["instrument"] == "CG1D"


def test_string_missing_tasks(GOOD_NON_INTERACTIVE):
    doc = load_file(GOOD_NON_INTERACTIVE)
    json_obj = json.loads(doc)
    del json_obj["tasks"]
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


@pytest.mark.parametrize(
    "facility,instrument", [("hfir", "CG1D"), ("HFIR", "cg1d"), ("HFIR", "SNAP"), ("HFIR", "junk"), ("SNS", "junk")]
)
def test_bad_instrument(facility, instrument, GOOD_NON_INTERACTIVE):
    doc = load_file(GOOD_NON_INTERACTIVE)
    json_obj = json.loads(doc)
    json_obj["facility"] = facility
    json_obj["instrument"] = instrument
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


def test_string_empty_function(GOOD_NON_INTERACTIVE):
    doc = load_file(GOOD_NON_INTERACTIVE)
    json_obj = json.loads(doc)
    json_obj["tasks"][0]["function"] = ""
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


@pytest.mark.parametrize(
    "bad_func_name",
    ["nonexistent.function", "toplevelfunction", "imars3d.backend.corrections.gamma_filter.GammaFilter"],
)
def test_string_bad_function(bad_func_name, GOOD_NON_INTERACTIVE):
    doc = load_file(GOOD_NON_INTERACTIVE)
    json_obj = json.loads(doc)
    json_obj["tasks"][0]["function"] = bad_func_name
    with pytest.raises(JSONValidationError):
        MockContainer(json.dumps(json_obj))


if __name__ == "__main__":
    pytest.main([__file__])
