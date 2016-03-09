#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, numpy as np, imars3d

dir = os.path.dirname(__file__)
# sinograms
sinograms = imars3d.io.ImageFileSeries(
    os.path.join(outdir, "sinogram_%i.npy"),
    name = "Sinogram", mode = 'w',
)


def test_recon():
    from imars3d.recon.use_tomopy import recon
    recon("range(150, 1330)", "np.arange(0, 182, .85)", outdir=outdir, sinogram_template=os.path.join(outdir, "sinogram_%i.npy"),
    return


def main():
    test_recon()
    return


if __name__ == '__main__': main()
