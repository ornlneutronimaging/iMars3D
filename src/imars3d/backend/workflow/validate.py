import importlib
from importlib.util import find_spec
import json
import jsonschema
from pathlib import Path
import sys
from typing import Any, Dict, Tuple, Union

FilePath = Union[Path, str]

# http://json-schema.org/learn/getting-started-step-by-step.html
SCHEMA_FILE = Path(__file__).parent / "schema.json"


def _load_schema():
    try:
        with open(SCHEMA_FILE, "r") as handle:
            schema = json.load(handle)
    except FileNotFoundError as e:
        raise RuntimeError(f"Failed to load schema from {SCHEMA_FILE}") from e

    if not schema:
        raise RuntimeError(f"Failed to load schema from {SCHEMA_FILE}")
    return schema


SCHEMA = _load_schema()
del _load_schema


def _validate_schema(json_obj: Dict, schema: Dict = SCHEMA) -> None:
    """Validate the data against the schema for jobs"""
    try:
        jsonschema.validate(json_obj, schema=schema)
    except jsonschema.ValidationError as e:
        raise JSONValidationError("While validation configuration file") from e


def _validate_instrument(facility, instrument, allowed_instr) -> None:
    if instrument not in allowed_instr:
        raise JSONValidationError(f"Instrument {instrument} is in list of allowed for {facility}: {allowed_instr}")


def _validate_facility_and_instrument(json_obj: Dict) -> None:
    FACILITIES = {"HFIR": ["CG1D"], "SNS": ["SNAP"]}

    facility = json_obj["facility"]
    if facility not in FACILITIES:
        raise JSONValidationError(
            f"Facility {facility} is missing in the list of allowed facilities: " + ", ".join(FACILITIES)
        )

    validate_instrument(facility, json_obj["instrument"], FACILITIES[facility])


def _function_parts(func_str: str) -> Tuple[str, str]:
    """Convert the function specification into a module and function name"""
    mod_str = ".".join(func_str.split(".")[:-1])
    func_str = func_str.split(".")[-1]
    return (mod_str, func_str)


def _function_exists(func_str: str) -> bool:
    """Returns True if the function exists"""
    mod_str, func_str = _function_parts(func_str)

    return bool(find_spec(mod_str, func_str))


def _validate_tasks_exist(json_obj: Dict) -> None:
    """Go through the list of tasks and verify that all tasks exist"""
    for step, task in enumerate(json_obj["tasks"]):
        func_str = task["function"].strip()
        if not func_str:
            # TODO need better exception
            raise JSONValidationError(f'Step {step} specified empty "function"')
        if "." not in func_str:
            raise JSONValidationError(f"Function '{func_str}' does not appear to be absolute specification")
        if not _function_exists(func_str):
            raise JSONValidationError(f'Step {step} specified nonexistent function "{func_str}"')


def _todict(obj: Union[Dict, Path, str]) -> Dict:
    """Convert the supplied object into a dict. Raise a TypeError if the object is not a type that has a conversion menthod."""
    if isinstance(obj, dict):
        return obj
    elif isinstance(obj, Path):
        with open(obj, "r") as handle:
            return json.load(handle)
    elif isinstance(obj, str):
        return json.loads(obj)
    else:
        raise TypeError(f"Do not know how to convert type={type(obj)} to dict")


class JSONValidationError(RuntimeError):
    """Custom exception for validation errors independent of what created them"""

    pass  # default behavior is good enough


class JSONValid:
    """Descriptor class that validates the json object

    See https://realpython.com/python-descriptors/"""

    def __init__(self, schema):
        self._schema = schema

    def __get__(self, obj, type=None) -> Dict:
        return obj._json

    def __set__(self, obj, value) -> None:
        obj._json = _todict(value)
        self._validate(obj._json)

    def _validate(self, obj: Dict) -> None:
        _validate_schema(obj, schema=self._schema)
        _validate_facility_and_instrument(obj)
        _validate_tasks_exist(obj)
