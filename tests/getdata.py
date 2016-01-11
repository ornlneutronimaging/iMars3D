#!/usr/bin/env python

# this script should be run root of iVenus pkg

path = "tests/iVenus_data_set"

import os
if not os.path.exists(path):
    cmd = "builders/download-testdata.py %s" % path
    if os.system(cmd):
        raise RuntimeError("%s failed" % cmd)
