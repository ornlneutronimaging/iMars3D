#!/usr/bin/env python3
"""Provides functions that are used in the auto reduction scripts."""

# standard imports
import json
import logging
import re
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

facility_position = -6
instrument_position = -5
experiment_position = -4


def auto_reduction_ready(data_file: Union[str, Path]) -> bool:
    """
    Check if the data file is ready for auto reduction.

    Expected directory tree for data_file is /SNS/CG1D/IPTS-XXXXX/raw/_IMAGING_TYPE_/

    Parameters
    ----------
    data_file
        The data file to check. Assumes the file exists

    Returns
    -------
    bool
        True if the data file is ready for auto reduction, False otherwise.
    """
    logger.info("Checking if scan has completed...")
    non_radiograph = {"dark-field": ["df"], "open-beam": ["ob"]}
    # /SNS/CG1D/IPTS-XXXXX/raw/_IMAGING_TYPE_/
    match = re.search(r"/raw/([-\w]+)/", str(data_file))
    if match:
        image_type = match.groups()[0]
        if image_type in non_radiograph["dark-field"] + non_radiograph["open-beam"]:
            logger.info("Scan is incomplete.")
            return False
    else:
        return False

    # TODO: check the scan-compete signal from either the TIFF file or the Nexus file or some other file or PV
    signal_scan_completed = True
    logger.info(f"Scan is {'' if signal_scan_completed else 'not '}complete.")
    return signal_scan_completed


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
    data_dict["facility"] = extracted_data[facility_position]  # "HFIR"
    data_dict["instrument"] = extracted_data[instrument_position]  # "CG1D"
    data_dict["ipts"] = extracted_data[experiment_position]  # "IPTS-25777"
    logger.info("Extract information from data file path.")
    return data_dict
