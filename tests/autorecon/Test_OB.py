#!/usr/bin/env python
import os, glob
from imars3d.CT_from_TIFF_metadata import autoreduce


ct_file_path = "/HFIR/CG1D/IPTS-20343/raw/ct_scans/20180905/20180906_CT_0042_183_000_1108.tiff"
autoreduce(
    ct_file_path,
    local_disk_partition='/SNSlocal2', 
    # clean_intermediate_files='archive',
    outdir='/HFIR/CG1D/IPTS-20343/shared/autoreduce/test',
    parallel_nodes=20)
