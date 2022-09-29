import json
from pathlib import Path
from typing import Union

FilePath = Union[Path, str]


def validates(json_str: str):
    # verify that the string is non-empty
    if len(json_str.strip()) == 0:
        raise json.JSONDecodeError("Empty string", json_str, 0)

    doc = json.loads(json_str)


def validate(filename: FilePath):
    filepath = Path(filename)
    with open(filepath, "r") as handle:
        doc = json.load(handle)
