import importlib
from importlib.util import find_spec
import json
import jsonschema
from pathlib import Path
import sys
from typing import Any, Dict, Tuple, Union

FilePath = Union[Path, str]

# JSON schema. Cut be here or in its own file
# http://json-schema.org/learn/getting-started-step-by-step.html
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "instrument": {"type": "string"},
        "ipts": {"type": "string"},
        "name": {"type": "string"},
        "workingdir": {"type": "string"},
        "outputdir": {"type": "string"},
        "tasks": {
            "type": "array",
            "minItems": 1,
            "items": {
                "properties": {
                    "name": {"type": "string"},
                    "function": {"type": "string"},
                    "inputs": {"type": "object"},
                    "outputs": {"type": "array"},
                },
                "required": ["name", "function", "inputs"],
            },
        },
    },
    "required": ["instrument", "ipts", "name", "workingdir", "outputdir", "tasks"],
}


def _validate_schema(json_obj: Any) -> None:
    """Validate the data against the schema for jobs"""
    try:
        jsonschema.validate(json_obj, schema=SCHEMA)
    except jsonschema.ValidationError as e:
        raise JSONValidationError("While validation configuration file") from e


def _function_parts(func_str: str) -> Tuple[str, str]:
    mod_str = ".".join(func_str.split(".")[:-1])
    func_str = func_str.split(".")[-1]
    return (mod_str, func_str)


def _function_exists(func_str: str) -> bool:
    # print('**********', func_str)
    mod_str, func_str = _function_parts(func_str)
    # print(mod_str, func_str)
    # print('mods:', mod_str, mod_str in sys.modules)
    # print('find_spec:', find_spec(mod_str, func_str))
    return bool(find_spec(mod_str, func_str))


def _validate_tasks(json_obj: Dict) -> None:
    for step, task in enumerate(json_obj["tasks"]):
        func_str = task["function"].strip()
        if not func_str:
            # TODO need better exception
            raise JSONValidationError(f'Step {step} specified empty "function"')
        if "." not in func_str:
            raise JSONValidationError(f"Function '{func_str}' does not appear to be absolute specification")
        if not _function_exists(func_str):
            raise JSONValidationError(f'Step {step} specified nonexistent function "{func_str}"')


def validates(json_str: str) -> None:
    # verify that the string is non-empty
    if len(json_str.strip()) == 0:
        raise json.JSONDecodeError("Empty string", json_str, 0)
    json_obj = json.loads(json_str)

    # validation
    _validate_schema(json_obj)
    _validate_tasks(json_obj)


def validate(filename: FilePath) -> None:
    filepath = Path(filename)
    with open(filepath, "r") as handle:
        json_obj = json.load(handle)

    # validation
    _validate_schema(json_obj)
    _validate_tasks(json_obj)


class JSONValidationError(RuntimeError):
    pass  # default behavior is good enough


class JSONValid:
    def __init__(self, schema):
        self._schema = schema

    def __get__(self, obj, objtype=None):
        return obj._json

    def __set__(self, obj, json):
        self._validate(json)
        obj._json = json

    def _validate(self, json_str) -> None:
        r"""check input json against class variable schema"""
        assert self._schema
        assert json
        return True
