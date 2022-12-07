#!/usr/bin/env python3
"""Util for imars3d."""

# standard imports
from datetime import datetime
import logging
import multiprocessing
import resource
from typing import Union


logger = logging.getLogger(__name__)


def clamp_max_workers(max_workers: Union[int, None]) -> int:
    """Calculate the number of max workers.

    If it isn't specified, return something appropriate for the system.
    """
    if max_workers is None:
        max_workers = 0

    result = min(resource.RLIMIT_NPROC, max(1, multiprocessing.cpu_count() - 2)) if max_workers <= 0 else max_workers

    # log if the value was different than what was asked for
    if max_workers == 0 and result != max_workers:
        logger.info(f"Due to system load, setting maximum workers to {result}")

    return result


def to_time_str(value: datetime = datetime.now()) -> str:
    """
    Convert the supplied datetime to a formatted string.

    Parameters
    ----------
    value:
        datetime object to format correctly

    Returns
    -------
        The datetime as YYYYMMDDhhmm
    """
    return value.strftime("%Y%m%d%H%M")
