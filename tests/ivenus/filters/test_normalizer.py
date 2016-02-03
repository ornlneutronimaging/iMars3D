#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from ivenus import io
from ivenus.filters import normalizer

def test_average():
    dir = os.path.dirname(__file__)
    pattern = os.path.join(dir, "..", "..", "iVenus_data_set", "turbine", "*DF*.fits")
    ic = io.imageCollection(pattern, name="Dark Field")
    a = normalizer.average(ic)
    return
    

def main():
    test_average()
    return

if __name__ == '__main__': main()

# End of file
