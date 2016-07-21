#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tell pytest to skip this test
import pytest
pytestmark = pytest.mark.skipif(True, reason="will run standalone")

import os
dir = os.path.dirname(__file__)
dir = os.path.join(dir, "..", "..", "iMars3D_data_set", "turbine", "full")
dir = os.path.abspath(dir)
print(dir)

def test():
    from imars3d.CT import CT
    ct = CT(
        dir,
        clean_on_the_fly=True, 
        vertical_range=slice(900, 1000)
    )
    ct.recon()
    return

if __name__ == '__main__': test()
