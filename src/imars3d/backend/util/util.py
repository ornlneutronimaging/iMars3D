#!/usr/bin/env python3
"""Util for imars3d."""

import resource
import multiprocessing

def clamp_max_workers(max_workers):
    return min(resource.RLIMIT_NPROC,max(1,multiprocessing.cpu_count()-2)) if max_workers <= 0 else max_workers