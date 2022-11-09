#!/usr/bin/env python3
"""Provides functions that are used in the auto reduction scripts."""
import json
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


def load_template_config(config_path) -> dict:
    """
    Load the template configuration file.

    Returns
    -------
    dict
        The template configuration file.
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

    Returns
    -------
    dict
        The extracted information.
    """
    logger.info("Extract information from data file path.")
    raise NotImplementedError
