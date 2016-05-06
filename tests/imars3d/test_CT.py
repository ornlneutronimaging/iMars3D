#!/usr/bin/env python

# tell pytest to skip this test
import pytest
pytestmark = pytest.mark.skipif(True, reason="need large dataset")

import os
datadir = os.path.join(
    os.path.dirname(__file__),
    '..',
    'iMars3D_large_dataset',
    )

def test():
    from imars3d.CT import CT
    turbine = os.path.join(datadir, 'reconstruction', 'turbine')
    ct = CT(turbine)
    return


def main():
    test()
    return

if __name__ == '__main__': main()
