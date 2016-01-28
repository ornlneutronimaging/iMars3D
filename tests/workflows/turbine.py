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
    os.path.join(datadir, "*CT*_%.3f_*.fits"),
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
    res = np.array(images[0].getData(), dtype=float)
    for i, im in enumerate(images[1:]):
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./(N-1)))
        console_out.flush()
        res += np.array(im.getData(), dtype=float)
        continue
    return res/N


def normalize(ct_series, df_images, ob_images, output_template, console_out):
    # compute dark field and open beam
    df_output = "df.npy"
    if not os.path.exists(df_output):
        df = average(df_images, "Dark field:", console_out)
        console_out.write("\n")
        np.save(df_output, df)
    else:
        df = np.load(df_output)
    ob_output = "ob.npy"
    if not os.path.exists(ob_output):
        ob = average(ob_images, "Open beam:", console_out)
        console_out.write("\n")
        np.save(ob_output, ob)
    else:
        ob = np.load(ob_output)
    # normalize
    prefix = "Normalize:"
    N = len(ct_series.angles)
    for i, angle in enumerate(ct_series.angles):
        fn = output_template % angle
        # skip over existing results
        if os.path.exists(fn): continue
        data = np.array(ct_series.getData(angle), dtype=float)
        data = (data-df)/ob
        f = ImageFile(fn)
        f.data = data
        f.save()
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    console_out.write("\n")
    return


normalized_ct_series = ImageSeries(
    os.path.join("normalized*_%7.3f.npy"),
    angles = np.arange(0, 182, .85),
    decimal_mark_replacement = ".",
    )
def compute_tilt(normalized_ct_series):
    tilt_out = "tilt.out"
    if os.path.exists(tilt_out):
        return float(open(tilt_out).read())
    from ivenus.tilt import phasecorrelation
    img = lambda angle: normalized_ct_series.getImageFile(angle)
    tilts = []
    for i in range(3):
        pc = phasecorrelation.PhaseCorrelation(logging_dir="log.tilt.%s"%i)
        tilt = pc(img(0+.85*i), img(180.2+.85*i))
        tilts.append(tilt)
        continue
    tilt = np.average(tilts)
    open(tilt_out, 'wt').write(str(tilt))
    return tilt
def check_tilt(tilt, normalized_ct_series):
    img = lambda angle: normalized_ct_series.getImageFile(angle)
    from ivenus.tilt import check
    check(tilt, img(0), img(180.20))
    return
tiltcorrected_ct_series = ImageSeries(
    os.path.join("tiltcorrected_%7.3f.npy"),
    angles = np.arange(0, 182, .85),
    decimal_mark_replacement = ".",
    )
def apply_tilt(tilt, normalized_ct_series, console_out):
    inputimg = lambda angle: normalized_ct_series.getImageFile(angle)
    outputimg = lambda angle: tiltcorrected_ct_series.getImageFile(
        angle, check_if_exists=False)
    from ivenus.tilt import apply
    prefix = "Apply tilt"
    N = len(normalized_ct_series.angles)
    for i,angle in enumerate(normalized_ct_series.angles):
        outimg = outputimg(angle)
        # skip over existing result
        if os.path.exists(outimg.path): continue
        apply(tilt, inputimg(angle), outimg)
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    console_out.write("\n")
    return


def reconstruct(ct_series, console_out):
    import tomopy
    proj = [];  theta = []; N = len(ct_series.angles)
    prefix = "Gather projection"
    for i,angle in enumerate(ct_series.angles):
        if i%3 != 0: continue
        theta.append(angle)
        proj.append(ct_series.getImageFile(angle).getData())
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    proj = np.array(proj, dtype=float)
    # reconstruct
    Y,X = proj[0].shape
    rec = tomopy.recon(
        proj[:, 923:1024, :], 
        theta=theta, center=X/2.,
        algorithm='gridrec', emission=False
    )
    tomopy.write_tiff_stack(rec, fname='recon', axis=0, overwrite=True)
    return


def main():
    normalize(
        ct_series, df_images, ob_images,
        "normalized_%7.3f.npy", sys.stdout
    )
    tilt = compute_tilt(normalized_ct_series)
    # print tilt
    # tilt = -1.86
    # check_tilt(tilt, normalized_ct_series)
    apply_tilt(tilt, normalized_ct_series, sys.stdout)
    reconstruct(tiltcorrected_ct_series, sys.stdout)
    return


if __name__ == '__main__': main()
