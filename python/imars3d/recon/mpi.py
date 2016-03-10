# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar
import os, sys, numpy as np


def recon(sinograms, theta, recon_series):
    """reconstruct from given sinograms by running reconstruction algorithms parallely

This is a wrapper application of recon_mpi.
The signature of this function is the same as .use_tomopy.recon.

    """
    # python code to run parallely
    sinogram_template = sinogram_
    py_code = """
from imars3d.recon.use_tomopy import recon_mpi
recon_mpi(layers=%(layers)s, theta=%(theta)s, 
    sinogram_template=%(sinogram_template)r, outdir=%(outdir)s, steps=10)
""" % locals()
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
    sinograms, theta, recon_series,
    stepsize=10, 
    recon=None):
    """reconstruction using mpi.
This method needs to be run on several mpi nodes to achieve
parallalization. sth similar to $ mpirun -np NODES python "code to call this method"

* theta: angles in radians
* recon: reconstruction method
    """
    import imars3d.io
    
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    
    totalN = len(sinograms)
    N = int(np.ceil(totalN*1. / size))
    start, stop = rank*N, min(totalN, (rank+1)*N)
    # print("node %s of %s handles %s" % (rank, size, layers))
    # print("N, start, stop=%s, %s, %s" % (N, start, stop))

    if recon is None:
        from .use_tomopy import recon_batch_singlenode as recon
    
    while start < stop:
        stop1 = min(start + stepsize, stop)
        print("node %s of %s working on %s:%s" % (rank, size, start, stop1))
        sinograms1 = sinograms[start:stop1]
        if not len(sinograms): continue
        recon_series1 = recon_series[start:stop1]
        try:
            recon(sinograms1, theta, recon_series1)
        except:
            print("node %s of %s: recon %s:%s failed" % (rank, size, start, stop1))
        start = stop1
        continue
    return


# End of file
