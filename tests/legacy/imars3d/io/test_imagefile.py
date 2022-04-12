#!/usr/bin/env python

import os, numpy as np
from imars3d import io


def test():
    _test_ext("tiff")
    _test_ext("npy")
    return


def _test_ext(ext):
    data = np.arange(300 * 400, dtype="float32")
    data.shape = 300, 400
    imgfile = io.ImageFile("img1.%s" % ext)
    imgfile.data = data
    imgfile.save()
    data2 = io.ImageFile("img1.%s" % ext).data
    assert (data == data2).all()
    return


def main():
    test()
    return


if __name__ == "__main__":
    main()
