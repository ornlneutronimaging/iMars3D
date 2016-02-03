#!/usr/bin/env python

"""
Desired Workflow. this script only have preprocessing steps: normalize, tilt correction, sinograms
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
from ivenus.io import ImageFileSeries, ImageFile

datadir = "../../../iVenus_large_dataset/reconstruction/turbine"
ct_series = ImageFileSeries(
    os.path.join(datadir, "*CT*_%.3f_*.fits"),
    identifiers = np.arange(0, 182, .85),
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
    N = len(ct_series.identifiers)
    for i, angle in enumerate(ct_series.identifiers):
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


normalized_ct_series = ImageFileSeries(
    os.path.join("normalized*_%7.3f.npy"),
    identifiers = np.arange(0, 182, .85),
    decimal_mark_replacement = ".",
    )
def compute_tilt(normalized_ct_series):
    tilt_out = "tilt.out"
    if os.path.exists(tilt_out):
        return float(open(tilt_out).read())
    from ivenus.tilt import phasecorrelation
    img = lambda angle: normalized_ct_series.getImage(angle)
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
    img = lambda angle: normalized_ct_series.getImage(angle)
    from ivenus.tilt import check
    check(tilt, img(0), img(180.20))
    return
tiltcorrected_ct_series = ImageFileSeries(
    os.path.join("tiltcorrected_%7.3f.npy"),
    identifiers = np.arange(0, 182, .85),
    decimal_mark_replacement = ".",
    mode = 'w',
    )
def apply_tilt(tilt, normalized_ct_series, console_out):
    inputimg = lambda angle: normalized_ct_series.getImage(angle)
    outputimg = lambda angle: tiltcorrected_ct_series.getImage(angle)
    from ivenus.tilt import apply
    prefix = "Apply tilt"
    N = len(normalized_ct_series.identifiers)
    for i,angle in enumerate(normalized_ct_series.identifiers):
        outimg = outputimg(angle)
        # skip over existing result
        if os.path.exists(outimg.path): continue
        apply(tilt, inputimg(angle), outimg)
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    console_out.write("\n")
    return


def project(ct_series, outdir, console_out):
    """convert ct image series to projection series"""
    if os.path.exists(outdir):
        msg = "%s existed, assume projection has already been done. skip this\n" % (
            outdir,)
        console_out.write(msg)
        return
    import tomopy
    data = []; N = len(ct_series.identifiers)
    prefix = "Read ct series"
    for i,angle in enumerate(ct_series.identifiers):
        # if i%3 != 0: continue
        data1 = ct_series.getImage(angle).getData()
        # data[data<=0] = 1.
        data1 = data1[100:-100, 100:-100]
        data.append(data1)
        console_out.write("\r%s: %2.0f%%" % (prefix, (i+1)*100./N))
        console_out.flush()
        continue
    console_out.write("\n"); console_out.flush()
    # project
    console_out.write("tomopy.normalize_bg..."); console_out.flush()
    proj = tomopy.normalize_bg(data) # , ncore=ncore)
    console_out.write("done\n"); console_out.flush()
    del data
    # remove negative intensities
    proj[proj<0] = 0
    # output
    console_out.write("tomopy.write_tiff_stack..."); console_out.flush()
    tomopy.write_tiff_stack(
        proj, fname=os.path.join(outdir, 'proj'), axis=1, overwrite=False)
    console_out.write("done\n"); console_out.flush()
    return


def reconstruct(proj_fn_template, layers, theta, console_out, outdir="recon"):
    """proj_fn_template: projection filename tempate
    layers: list of integers for layers to be reconstructed
    theta: sample rotation angle in radian
    """
    import tomopy
    proj = tomopy.read_tiff_stack(proj_fn_template % layers[0], layers, digit=5)
    proj = np.swapaxes(proj, 0,1)
    Y,X = proj[0].shape
    # reconstruct
    console_out.write("tomopy.reconstruct..."); console_out.flush()
    rec = tomopy.recon(
        proj,
        theta=theta, center=X/2.,
        algorithm='gridrec', emission=False,
        ncore = 1,
    )
    console_out.write("done\n"); console_out.flush()
    # output
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    console_out.write("tomopy.write_tiff_stack..."); console_out.flush()
    tomopy.write_tiff_stack(
        rec, fname=os.path.join(outdir, 'recon'), axis=0, overwrite=True)
    console_out.write("done\n"); console_out.flush()
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
    project(tiltcorrected_ct_series, "proj", sys.stdout)
    # theta = np.array(ct_series.identifiers, dtype=float)
    # theta *= np.pi/180.
    # proj_fn_template = "proj/proj_%05i.tiff"
    # layers = range(150,1330, 10)
    # reconstruct(proj_fn_template, layers, theta, sys.stdout, outdir="recon")
    return


if __name__ == '__main__': main()
