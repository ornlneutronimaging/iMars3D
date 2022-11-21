#!/usr/bin/env python3
"""Util for imars3d."""

# standard imports
from datetime import datetime
import multiprocessing
import resource
from typing import Union


def clamp_max_workers(max_workers: Union[int, None]) -> int:
    """Calculate the number of max workers.

    If it isn't specified, return something appropriate for the system.
    """
    if max_workers is None:
        max_workers = 0
    return min(resource.RLIMIT_NPROC, max(1, multiprocessing.cpu_count() - 2)) if max_workers <= 0 else max_workers


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
