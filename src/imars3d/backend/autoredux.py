#!/usr/bin/env python3
"""Provides functions that are used in the auto reduction scripts."""
import json
import logging
from typing import Union
from pathlib import Path

logger = logging.getLogger(__name__)


def auto_reduction_ready(data_file: str) -> bool:
    """
    Check if the data file is ready for auto reduction.

    Parameters
    ----------
    data_file
        The data file to check.

    Returns
    -------
    bool
        True if the data file is ready for auto reduction, False otherwise.
    """
    logger.info("Check if data is ready for auto reduction.")
    raise NotImplementedError


def load_template_config(config_path: Union[str, Path]) -> dict:
    """
    Load the given path as a template configuration file.

    Parameters
    ----------
    config_path: Union[str, pathlib.Path]
        Path of template config to be loaded

    Returns
    -------
    dict
        The template configuration file.

    Raises
    ------
    FileNotFoundError
        If the given path cannot be resolved
    JSONDecodeError
        If the resolved file cannot be parsed as JSON
    """
    logger.info("Loading template configuration file: %s", config_path)

    with open(config_path, "r") as template_config:
        config = json.load(template_config)
        return config


def extract_info_from_path(data_file: str) -> dict:
    """
    Extract information from the data file path.

    Parameters
    ----------
    data_file
        The data file to extract information from.
        ex. /HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man/20191029_ironman_small_0070_000_000_0002.tiff

    Returns
    -------
    dict
        The extracted information.
    """
    extracted_data = data_file.split("/")
    data_dict = {}
    # index from right to be agnostic of root
    data_dict["facility"] = extracted_data[-6]          # "HFIR"
    data_dict["instrument"] = extracted_data[-5]        # "CG1D"
    data_dict["ipts"] =  extracted_data[-4]             # "IPTS-25777"
    logger.info("Extract information from data file path.")
    return data_dict
