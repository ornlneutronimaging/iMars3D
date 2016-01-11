#!/usr/bin/env python

from __future__ import print_function
import sys, os, tempfile, subprocess as sp, shutil

help = """
$ %s <output-dir>

download test data from dropbox and expand them into the given output directory
""" % sys.argv[0]

if len(sys.argv) < 2:
    print(help)
    sys.exit(1)

OUT=os.path.abspath(sys.argv[1])
WORK=tempfile.mkdtemp()
os.makedirs(OUT)
cmd = "wget -O iVenus_data_set.zip https://www.dropbox.com/sh/g5tho8czs8fi5lm/AAAZsZmqdqWLuo5c-OXtRlcJa?dl=1"
sp.check_call(cmd.split(), cwd=WORK)
cmd = "unzip %s/iVenus_data_set.zip" % WORK
sp.call(cmd.split(), cwd=OUT)
shutil.rmtree(WORK)
