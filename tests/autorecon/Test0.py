#!/usr/bin/env python

"""Test basic functionality:

* skip reconstruction when CT is not done
"""

import os, glob
from imars3d.CT_from_TIFF_metadata import autoreduce


dir = "/HFIR/CG1D/IPTS-21115/raw/ct_scans/July26_2018/"
files = glob.glob(os.path.join(dir, '*.tiff'))

for f in files[:5]:
    autoreduce(f, local_disk_partition='/tmp', parallel_nodes=20)

    
ct_file_path = "/HFIR/CG1D/IPTS-21115/raw/ct_scans/July26_2018/20180727_Huggies_bottom_0015_359_445_2319.tiff"
autoreduce(ct_file_path, local_disk_partition='/tmp', parallel_nodes=20)
