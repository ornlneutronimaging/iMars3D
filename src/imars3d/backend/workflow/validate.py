#!/usr/bin/enb python3
"""iMars3D's config validation module."""
# standard imports
from collections.abc import Iterable
from importlib.util import find_spec
import json
import jsonschema
from pathlib import Path
from typing import Dict, Tuple, Union

FilePath = Union[Path, str]
JsonInputTypes = Union[str, dict, Path]

# http://json-schema.org/learn/getting-started-step-by-step.html
SCHEMA_FILE = Path(__file__).parent / "schema.json"
# reverse strings for parameters denoting metadata or output items from the workflow steps
GLOBAL_PARAMS = {
    "facility",
    "instrument",
    "ipts",
    "workingdir",
    "outputdir",
    "ct",  # array of radiograph intensities
    "ob",  # array of open bean intensities
    "dc",  # array of dark current intensities
    "tilt_angle",
    "rot_center",
    "rot_angles",
}


def _load_schema():
    """Load default schema."""
    try:
        with open(SCHEMA_FILE, "r") as handle:
            schema = json.load(handle)
    except FileNotFoundError as e:
        raise RuntimeError(f"Failed to load schema from {SCHEMA_FILE}") from e

    if not schema:
        raise RuntimeError(f"Failed to load schema from {SCHEMA_FILE}")
    return schema


SCHEMA: dict = _load_schema()
del _load_schema


def _validate_schema(json_obj: Dict) -> None:
    """Validate the data against the schema for jobs.

    Parameters
    ----------
    json_obj : Dict
        The data to validate

    Raises
    ------
    JSONValidationError
        If the data does not validate against the schema

    Returns
    -------
    None
    """
    try:
        jsonschema.validate(json_obj, schema=SCHEMA)
    except jsonschema.ValidationError as e:
        raise JSONValidationError("While validation configuration file") from e


def _validate_facility(json_obj: Dict) -> None:
    facilities = {"HFIR", "SNS"}
    facility = json_obj["facility"]
    if facility not in facilities:
        raise JSONValidationError(
            f"Facility {facility} is missing in the list of allowed facilities: " + ", ".join(facilities)
        )


def _validate_instrument(json_obj: Dict, allowed_instr: set) -> None:
    instrument = json_obj["instrument"]
    if instrument not in allowed_instr:
        raise JSONValidationError(f"Instrument {instrument} is missing in list {allowed_instr}")


def _validate_facility_and_instrument(json_obj: Dict) -> None:
    _validate_facility(json_obj)
    allowed_instr = {"HFIR": {"CG1D"}, "SNS": {"SNAP"}}[json_obj["facility"]]
    _validate_instrument(json_obj, allowed_instr)


def function_parts(func_str: str) -> Tuple[str, str]:
    """Convert the function specification into a module and function name."""
    mod_str = ".".join(func_str.split(".")[:-1])
    func_str = func_str.split(".")[-1]
    return (mod_str, func_str)


def _function_exists(func_str: str) -> bool:
    """Return True if the function exists."""
    mod_str, func_str = function_parts(func_str)

    return bool(find_spec(mod_str, func_str))


def _validate_tasks_exist(json_obj: Dict) -> None:
    """Go through the list of tasks and verify that all tasks exist."""
    for step, task in enumerate(json_obj["tasks"]):
        func_str = task["function"].strip()
        if not func_str:
            # TODO need better exception
            raise JSONValidationError(f'Step {step} specified empty "function"')
        if "." not in func_str:
            raise JSONValidationError(f"Function '{func_str}' does not appear to be absolute specification")
        if not _function_exists(func_str):
            raise JSONValidationError(f'Step {step} specified nonexistent function "{func_str}"')


def _todict(obj: JsonInputTypes) -> Dict:
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
    """Custom exception for validation errors independent of what created them."""

    pass  # default behavior is good enough


class JSONValid:
    """Descriptor class that validates the json object.

    See https://realpython.com/python-descriptors/
    """

    def __get__(self, obj, type=None) -> Dict:
        """Return the json object."""
        return obj._json

    def __set__(self, obj, value) -> None:
        """Validate the json object."""
        obj._json = _todict(value)
        self._validate(obj._json)

    def required(self, queryset: Iterable) -> bool:
        r"""Check if a set of input parameters are required by the schema.

        Parameters
        ----------
        queryset
            list of input parameters.

        Returns
        -------
        bool
            True if all the input parameters are required by the schema.
        """
        # cat the set of query parameters into a python set
        queryset = {queryset} if isinstance(queryset, str) else set(queryset)
        # check if the set queryset is contained in the set of required parameters
        return len(queryset - set(SCHEMA.get("required", {}))) == 0

    def _validate(self, obj: Dict) -> None:
        _validate_schema(obj)
        # Additional validations only when required by the schema
        if self.required({"facility", "instrument"}):
            _validate_facility_and_instrument(obj)
        if self.required("tasks"):
            _validate_tasks_exist(obj)
