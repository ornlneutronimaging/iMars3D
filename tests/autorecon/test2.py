#!/usr/bin/env python

import os, glob
from imars3d.CT_from_TIFF_metadata import autoreduce

ct_file_path = "/HFIR/CG1D/IPTS-21115/raw/ct_scans/July26_2018/20180727_Huggies_bottom_0015_359_910_2322.tiff"
autoreduce(ct_file_path, local_disk_partition='/SNSlocal2', parallel_nodes=20)
