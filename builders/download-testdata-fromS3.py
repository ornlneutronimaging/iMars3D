#!/usr/bin/env python

from __future__ import print_function
import sys, os, tempfile, subprocess as sp, shutil

help = """
$ %s <output-dir>

download test data from S3 to the output dir
""" % sys.argv[0]

if len(sys.argv) < 2:
    print(help)
    sys.exit(1)

OUT=os.path.abspath(sys.argv[1])
if not os.path.exists(OUT):
    os.makedirs(OUT)
cmd = "aws s3 sync s3://imars3d-testdata/ %s/ --profile imars3d_tester" % OUT
sp.check_call(cmd.split())
