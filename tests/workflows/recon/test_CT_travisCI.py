#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This test is to be run by travis CI.

$ python THIS.py test
$ python THIS.py test2
"""

# tell pytest to skip this test
import pytest
pytestmark = pytest.mark.skipif(True, reason="will run standalone")

import os
dir = os.path.dirname(__file__)
dir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine", "full")
dir = os.path.abspath(dir)
print(dir)

import imars3d
imars3d.configuration['parallelization']['max_nodes'] = 2
from imars3d.CT import CT

def test(nodes):
    ct = CT(
        dir,
        clean_on_the_fly=True, 
        vertical_range=slice(900, 1000),
        parallel_nodes=nodes,
    )
    ct.recon(tilt=-1.40, explore_rot_center=False)
    return

def test2(nodes):
    ct = CT(
        dir,
        clean_on_the_fly=True, 
        vertical_range=slice(900, 1000),
        parallel_nodes=nodes,
        skip_df = True
    )
    ct.recon(tilt=-1.40, explore_rot_center=False)
    return


def main():
    nodes = os.environ.get('NODES')
    if nodes:
        nodes = int(nodes)
    print("Processing using %s nodes" % (nodes or 'all'))

    import sys
    name = sys.argv[1] if len(sys.argv)>1 else 'test'
    method = eval(name)
    method(nodes)
    return


if __name__ == '__main__': main()
