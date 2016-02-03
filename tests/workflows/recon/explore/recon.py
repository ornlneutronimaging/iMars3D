#!/usr/bin/env python

import os, sys, numpy as np
from ivenus.io import ImageFileSeries
ct_series = ImageFileSeries(
    os.path.join("tiltcorrected_%7.3f.npy"),
    identifiers = np.arange(0, 182, .85),
    decimal_mark_replacement = ".",
    )

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
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    
    alllayers = range(150,1330)
    totalN = len(alllayers)
    N = totalN // size
    start, stop = rank*N, (rank+1)*N
    layers = alllayers[start:stop]
    # print len(layers)
    
    theta = np.array(ct_series.identifiers, dtype=float)
    theta *= np.pi/180.
    proj_fn_template = "proj/proj_%05i.tiff"
    step = 10
    for i in range(len(layers)//step+1):
        layers1 = layers[i*step: (i+1)*step]
        if not layers1: continue
        outdir = "recon/node%s/step%s" % (rank, i)
        print outdir
        reconstruct(proj_fn_template, layers1, theta, sys.stdout, outdir)
        continue
    return


if __name__ == '__main__': main()
