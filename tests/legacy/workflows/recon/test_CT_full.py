#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This test script is to be run by hand.
"""

# tell pytest to skip this test
import pytest

pytestmark = pytest.mark.skipif(True, reason="only run mannually")

import os

dir = os.path.dirname(__file__)
dir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine", "full")
dir = os.path.abspath(dir)
print(dir)


def test():
    from imars3d.CT import CT

    ct = CT(dir)
    ct.recon()
    return


if __name__ == "__main__":
    test()
