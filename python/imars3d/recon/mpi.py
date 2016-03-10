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
    sinogram_template="sinograms/sinogram_%05i.tiff", 
    recon_template="recon/recon_%05i.tiff",
    stepsize=10, 
    recon=None):
    """reconstruction using mpi.
This method needs to be run on several mpi nodes to achieve
parallalization. sth similar to $ mpirun -np NODES python "code to call this method"

* layers: list of integers
* theta: angles in radians
* recon: reconstruction method
    """
    import imars3d.io
    
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

    if recon is None:
        from .use_tomopy import recon_batch_singlenode as recon
    
    for i in range(len(layers)//stepsize+1):
        layers1 = layers[i*stepsize: (i+1)*stepsize]
        print("node %s of %s working on %s" % (rank, size, layers1))
        if not layers1: continue
        
        sinograms = imars3d.io.ImageFileSeries(
            sinogram_template,
            name = "Sinogram", identifiers = layers1,
        )
        recon_series = imars3d.io.ImageFileSeries(
            recon_template,
            mode = 'w', name = "Reconstructed", identifiers=layers1,
        )
        recon(sinograms, theta, recon_series)
        continue
    return


# End of file
