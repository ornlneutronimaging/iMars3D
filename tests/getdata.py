#!/usr/bin/env python

# this script should be run root of iMars3D pkg

path = "tests/iMars3D_data_set"

import os
if not os.path.exists(path):
    cmd = "builders/download-testdata-fromS3.py %s" % path
    if os.system(cmd):
        raise RuntimeError("%s failed" % cmd)
