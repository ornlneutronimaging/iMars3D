# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar
import os, sys, numpy as np


def recon_mpi_app(
    layers, theta, nodes=None, outdir="out",
    signogram_template="sinograms/sinogram_%05i.tiff"):
    """reconstruction

This is a wrapper application of recon_mpi.

Example:
    recon("range(155, 1550)", "np.arange(0, 52, 8.5)", sinogram_template
    """
    py_code = "from imars3d.recon.use_tomopy import recon_mpi; recon_mpi(layers=%(layers)s, theta=%(theta)s, sinogram_template=%(sinogram_template)r, outdir=%(outdir)s, steps=10)" % locals()
    import tempfile
    dir = tempfile.mkdtemp()
    pyfile = os.path.join(dir, "recon.py")
    open(pyfile, 'wt').write(py_code)
    
    if not nodes:
        import multiprocessing as mp
        nodes = mp.cpu_count() - 1
    nodes = max(nodes, 1)
    
    cmd = 'mpi run -np %(nodes)s python %(pyfile)s' % locals()
    if os.system(cmd):
        raise RuntimeError("%s failed" % cmd)
    return


def recon_mpi(
    layers, theta,
    signogram_template="sinograms/sinogram_%05i.tiff", 
    steps=10, outdir="out"):
    """reconstruction using mpi.
This method needs to be run on several mpi nodes to achieve
parallalization. sth similar to $ mpirun -np NODES python "code to call this method"

* layers: list of integers
* theta: angles in degrees
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
        outdir1 = os.path.join(outdir, "recon/node%s/step%s" % (rank, i))
        print outdir1
        recon_mpi_onenode(sinogram_template, layers1, theta, sys.stdout, outdir1)
        continue
    return


def recon(
    sinogram_template, layers, theta, console_out,
    outdir="recon"):
    """Use tomopy for reconstruction

    sinogram_template: sinogram filename tempate
    layers: list of integers for layers to be reconstructed
    theta: sample rotation angle in radian
    """
    import tomopy, imars3d.io
    # proj = tomopy.read_tiff_stack(
    #    sinogram_template % layers[0], layers, digit=5)
    # proj = np.swapaxes(proj, 0,1)
    # Y,X = proj[0].shape
    sinograms = imars3d.io.ImageFileSeries(
        sinogram_template, name = "Sinogram", identifiers=layers,
    )
    proj = [sinograms[i].data for i in range(layers)]
    proj = np.array(proj)
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


# End of file
