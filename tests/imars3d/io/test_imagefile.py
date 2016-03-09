#!/usr/bin/env python

import os, numpy as np
from imars3d import io

def test():
    data = np.arange(300*400, dtype="float32")
    data.shape = 300, 400
    imgfile = io.ImageFile("img1.tiff")
    imgfile.data = data
    imgfile.save()
    return


def main():
    test()
    return


if __name__ == "__main__": main()
