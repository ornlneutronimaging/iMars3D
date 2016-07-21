#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

if __name__ == '__main__': test()
