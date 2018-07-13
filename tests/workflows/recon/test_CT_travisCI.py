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
imars3d.configuration['parallelization']['max_nodes'] = 20
from imars3d.CT import CT

def test(nodes):
    ct = CT(
        dir,
        clean_intermediate_files = 'on_the_fly', 
        vertical_range=slice(900, 1000),
        parallel_nodes=nodes,
    )
    ct.recon(tilt=-1.40, explore_rot_center=False)
    assert not os.path.exists('work')
    return

def test2(nodes):
    ct = CT(
        dir,
        clean_intermediate_files='archive',
        vertical_range=slice(900, 1000),
        parallel_nodes=nodes,
        skip_df = True
    )
    ct.recon(tilt=-1.40, explore_rot_center=False)
    assert not os.path.exists('work')
    import glob
    assert glob.glob('out/work-*')
    return

def test3(nodes):
    ct = CT(
        dir,
        clean_intermediate_files = None,
        vertical_range=slice(900, 1000),
        parallel_nodes=nodes,
    )
    ct.recon(tilt=-1.40, explore_rot_center=False)
    assert os.path.exists('work')
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
