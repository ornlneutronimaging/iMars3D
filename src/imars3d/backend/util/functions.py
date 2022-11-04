#!/usr/bin/env python3
"""Util for imars3d."""

import resource
import multiprocessing
from typing import Union


def clamp_max_workers(max_workers: Union[int, None]) -> int:
    """Calculate the number of max workers.

    If it isn't specified, return something appropriate for the system.
    """
    if max_workers is None:
        max_workers = 0
    return min(resource.RLIMIT_NPROC, max(1, multiprocessing.cpu_count() - 2)) if max_workers <= 0 else max_workers
