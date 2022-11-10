#!/usr/bin/env python3
"""Provides functions that are used in the auto reduction scripts."""
import logging

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


def load_template_config() -> dict:
    """
    Load the template configuration file.

    Returns
    -------
    dict
        The template configuration file.
    """
    logger.info("Load template configuration file.")
    raise NotImplementedError


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
