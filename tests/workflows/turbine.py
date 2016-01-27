#!/usr/bin/env python

"""
Workflow
* crop images 
* filter spots 
* normalize
* normalize for beam intensity fluctuation: select ROI
* filter rings
* correct axis tilt
* sinograms
* parallel beam reconstruction
"""

import os, glob, numpy as np, sys
from ivenus.io import ImageSeries, ImageFile

datadir = "../iVenus_large_dataset/reconstruction/turbine"
ct_series = ImageSeries(
    os.path.join(datadir, "*CT_%.3f_*.fits"),
    angles = np.arange(0, 182, .85),
    )
df_images = [
    ImageFile(p) 
    for p in glob.glob(os.path.join(datadir, "*DF*.fits"))
    ]
# print [im.path for im in df_images]
ob_images = [
    ImageFile(p) 
    for p in glob.glob(os.path.join(datadir, "*OB*.fits"))
    ]


def average(images, prefix, console_out):
    N = len(images)
    assert N
    res = images[0].getData()
    for i, im in enumerate(images[1:]):
        console_out.write("\r%s: %2.0f%%" % (prefix, i*100./N))
        console_out.flush()
        res += im.getData()
        continue
    return res/len(images)    


def normalize(ct_series, df_images, ob_images):
    df = average(df_images, "Dark field:", sys.stdout)
    sys.stdout.write("\n")
    ob = average(ob_images, "Open beam:", sys.stdout)
    sys.stdout.write("\n")
    return


def main():
    normalize(ct_series, df_images, ob_images)
    return


if __name__ == '__main__': main()
