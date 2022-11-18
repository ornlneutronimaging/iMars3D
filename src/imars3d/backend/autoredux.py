#!/usr/bin/env python3
"""Provides functions that are used in the auto reduction scripts."""

# standard imports
import json
import logging
from pathlib import Path
import os
import re
from string import Template
from typing import Union

# parent logger for all loggers instantiated in the auto-reduction scripts
logger = logging.getLogger(__name__)


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
    # canonical data_file path: /SNS/CG1D/IPTS-XXXXX/raw/_IMAGING_TYPE_/
    match = re.search(r"/raw/([-\w]+)/", str(data_file))
    if match:
        image_type = match.groups()[0]
        if image_type in non_radiograph["dark-field"] + non_radiograph["open-beam"]:
            logger.info("The input image is not a radiograph. It's assumed the scan is incomplete.")
            return False
    else:
        logger.error("non-canonical data file path")
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


def extract_info_from_path(data_file: Union[str, Path]) -> dict:
    """
    Extract information from the data file path.

    The data file path must conform to the following directory hierarchy
    .. code-block:: sh

       /FACILITY/INSTRUMENT/IPTS/raw/[PREPATH]/ct_scans/[SUBPATH]/IMAGENAME.tiff

    ``PREPATH`` and ``SUBPATH`` are optional and can encompass one or more directories.

    Examples
    --------
    .. code-block:: sh

       /HFIR/CG1D/IPTS-25777/raw/ct_scans/20191029_ironman_small_0070_000_000_0002.tiff
       /HFIR/CG1D/IPTS-25777/raw/2019_Oct/ct_scans/20191029_ironman_small_0070_000_000_0002.tiff
       /HFIR/CG1D/IPTS-25777/raw/2019_Oct/29/ct_scans/20191029_ironman_small_0070_000_000_0002.tiff
       /HFIR/CG1D/IPTS-25777/raw/2019_Oct/29/ct_scans/iron_man/XYZ/20191029_ironman_small_0070_000_000_0002.tiff

    Parameters
    ----------
    data_file
        The data file to extract information

    Returns
    -------
    dict
        The extracted information with the following keys:
        facility, instrument, ipts, prepath, subpath
    """
    # Assuming the path is an absolute path
    facility_position = 1
    instrument_position = 2
    experiment_position = 3
    raw_position = 4

    extracted_data = Path(data_file).parts
    assert extracted_data[0] == os.path.sep, f"Path {str(data_file)} is not an absolute path"

    # Extract FACILITY, INSTRUMENT, and IPTS
    data_dict = {}
    data_dict["facility"] = extracted_data[facility_position]  # "HFIR"
    data_dict["instrument"] = extracted_data[instrument_position]  # "CG1D"
    data_dict["ipts"] = extracted_data[experiment_position]  # "IPTS-25777"

    # Locate the index of the radiographs directory in list `extracted_data`
    ct_position = -1
    for i in range(1 + raw_position, len(extracted_data)):
        if extracted_data[i] in ["ct_scans", "ct", "radiographs"]:
            ct_position = i
            break
    assert ct_position > raw_position, "No radiographs directory found"
    data_dict["radiograph"] = extracted_data[ct_position]

    # Extract PREPATH and SUBPATH
    data_dict["prepath"] = os.path.sep.join(extracted_data[1 + raw_position : ct_position])
    data_dict["subpath"] = os.path.sep.join(extracted_data[1 + ct_position : -1])

    logger.info("Extract information from data file path.")
    return data_dict


def substitute_template(config: dict, values: dict) -> dict:
    r"""Update the template configuration with actual values.

    Parameters
    ----------
    config
        dictionary resulting from loading the template JSON configuration file
    values
        dictionary resulting from scanning the path to the input radiograph
        with function `extract_info_from_path`

    Returns
    -------
        dictionary with template keywords substituted with actual values
    """
    # Compose ct_dir, ob_dir, and dc_dir as PREPATH/IMAGE_TYPE/SUBPATH
    raw_path = Path("/")
    for subdir in ("facility", "instrument", "ipts"):
        raw_path = raw_path / values[subdir]
    pre_path = raw_path / "raw" / values["prepath"]
    values.update(
        {
            "ctdir": str(pre_path / values["radiograph"] / values["subpath"]),
            "obdir": str(pre_path / "ob" / values["subpath"]),
            "dcdir": str(pre_path / "df" / values["subpath"]),
        }
    )
    assert {"facility", "instrument", "ipts", "name", "workingdir", "outputdir", "tasks"}.issubset(
        set(config.keys())
    ), "Config template dict is missing keys."
    template = Template(json.dumps(config))
    return json.loads(template.substitute(**values))
