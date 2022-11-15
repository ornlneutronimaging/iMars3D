#!/usr/bin/env python3
"""Configuration file handler for the imars3d."""
import json
from pathlib import Path
from typing import Union


def save_config(
    config_dict: dict,
    filepath: Union[str, Path],
):
    """
    Save a config dict to a file.

    Parameters
    ----------
    config_dict : dict
        The config dict to save.
    filepath : str
        The filepath to save the config dict to.
    """
    # sanity check
    filepath = Path(filepath)
    if filepath.suffix not in (".json", ".JSON"):
        raise ValueError("incorrect config file extension")

    # make the directory if not exist
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # now write to disk
    with open(filepath, "w") as outfile:
        json.dump(config_dict, outfile, indent=2, sort_keys=False)
