#!/usr/bin/env python3
"""
Configuration file handler for the imars3d.
"""
import json
from pathlib import Path


def save_config(
    config_dict: dict,
    filepath: str,
):
    # sanity check
    filepath = Path(filepath)
    if filepath.suffix not in (".json", ".JSON"):
        raise ValueError("incorrect config file extension")

    # make the directory if not exist
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # now write to disk
    with open(filepath, "w") as outfile:
        json.dump(config_dict, outfile, indent=2, sort_keys=False)
