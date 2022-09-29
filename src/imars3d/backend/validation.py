import json
import jsonschema
from pathlib import Path
from typing import Any, Union

FilePath = Union[Path, str]

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
    jsonschema.validate(json_obj, schema=SCHEMA)


def validates(json_str: str) -> None:
    # verify that the string is non-empty
    if len(json_str.strip()) == 0:
        raise json.JSONDecodeError("Empty string", json_str, 0)

    json_obj = json.loads(json_str)

    _validate_schema(json_obj)


def validate(filename: FilePath) -> None:
    filepath = Path(filename)
    with open(filepath, "r") as handle:
        json_obj = json.load(handle)

    _validate_schema(json_obj)
