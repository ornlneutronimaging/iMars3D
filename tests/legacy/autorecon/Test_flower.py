#!/usr/bin/env python

import os, glob
from imars3d.CT_from_TIFF_metadata import autoreduce

ct_file_path = "/HFIR/CG1D/IPTS-21123/raw/ct_scans/July28_2018/20180729_flower_0015_360_995_2329.tiff"

autoreduce(ct_file_path, local_disk_partition="/SNSlocal2", parallel_nodes=20, crop_window=(0, 0, 2047, 2000), tilt=0)
