#!/usr/bin/env python3
"""
This module provides functions that are used in the auto reduction scripts.
"""
import logging

logger = logging.getLogger(__name__)


def auto_reduction_ready(data_file: str) -> bool:
    """
    Checks if the data file is ready for auto reduction.

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
    Loads the template configuration file.

    Returns
    -------
    dict
        The template configuration file.
    """
    logger.info("Load template configuration file.")
    raise NotImplementedError


def extract_info_from_path(data_file: str) -> dict:
    """
    Extracts information from the data file path.

    Parameters
    ----------
    data_file
        The data file to extract information from.

    Returns
    -------
    dict
        The extracted information.
    """
    logger.info("Extract information from data file path.")
    raise NotImplementedError
