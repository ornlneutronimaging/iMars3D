# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar

from .AbstractComponent import AbstractComponent

class TiltCalculation(AbstractComponent):
    
    def __init__(self, workdir):
        self.workdir = workdir
        return
    
    def __call__(self, ct_series):
        workdir = self.workdir
        from ..tilt import compute
        return compute(ct_series, workdir)


import os, sys, numpy as np

def recon_mpi_onenode(
    sinogram_template, layers, theta, console_out,
    outdir="recon"):
    """sinogram_template: sinogram filename tempate
    layers: list of integers for layers to be reconstructed
    theta: sample rotation angle in radian
    """
    import tomopy
    proj = tomopy.read_tiff_stack(
        sinogram_template % layers[0], layers, digit=5)
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


def recon_mpi(
    layers, theta,
    signogram_template="sinograms/sinogram_%05i.tiff", 
    steps=10):
    """layers: list of integers
    theta: angles in degrees
    """
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    
    alllayers = layers
    totalN = len(alllayers)
    N = totalN // size
    start, stop = rank*N, (rank+1)*N
    layers = alllayers[start:stop]
    # print len(layers)
    
    theta *= np.pi/180.
    for i in range(len(layers)//steps+1):
        layers1 = layers[i*steps: (i+1)*steps]
        if not layers1: continue
        outdir = "recon/node%s/step%s" % (rank, i)
        print outdir
        recon_mpi_onenode(sinogram_template, layers1, theta, sys.stdout, outdir)
        continue
    return


# End of file
