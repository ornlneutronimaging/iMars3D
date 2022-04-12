# -*- python -*-
# -*- coding: utf-8 -*-

import os

# import sys
import numpy as np
import tempfile
import pickle
import imars3d

import progressbar
from imars3d import configuration

pb_config = configuration["progress_bar"]

# maximum loop avoid infinite while-loop
# TODO FIXME - need a better value or configurable value
MAX_LOOP = 100000


def recon(sinograms, theta, recon_series, nodes=None, **kwds):
    """reconstruct from given sinograms by running reconstruction algorithms parallely

    This is a wrapper application of recon_mpi.
    This is a method that users should use, not recon_mpi below.
    The signature of this function is the same as .use_tomopy.recon.

    """
    # python code to run parallely
    py_code_template = """
import pickle
kargs = pickle.load(open(%(kargs_pkl)r, 'rb'))

from imars3d.recon.mpi import recon_mpi
recon_mpi(**kargs)
"""

    dir = tempfile.mkdtemp()
    # save params
    kargs_pkl = os.path.join(dir, "kargs.pkl")
    kargs = dict(sinograms=sinograms, theta=theta, recon_series=recon_series)
    kargs.update(kwds)
    with open(kargs_pkl, "wb") as ostream:
        pickle.dump(kargs, ostream)
    # write python code
    pycode = py_code_template % locals()
    pyfile = os.path.join(dir, "recon.py")
    with open(pyfile, "wt") as ostream:
        ostream.write(pycode)
    # print(kargs_pkl, pyfile)
    # cpus
    if not nodes:
        import psutil

        nodes = psutil.cpu_count() - 1
    nodes = max(nodes, 1)
    nodes = min(nodes, imars3d.configuration["parallelization"]["max_nodes"])
    # shell cmd
    cmd = "mpirun -np %(nodes)s python %(pyfile)s" % locals()
    from ..shutils import exec_redirect_to_stdout

    exec_redirect_to_stdout(cmd)
    return cmd


def recon_mpi(sinograms, theta, recon_series, stepsize=10, center=None, recon=None, **kwds):
    """reconstruction using mpi.
    This method needs to be run on several mpi nodes to achieve
    parallalization. sth similar to $ mpirun -np NODES python "code to call this method"

    * theta: angles in radians
    * recon: reconstruction method
    """
    import logging

    logger = logging.getLogger("mpi")
    import imars3d.io

    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    totalN = len(sinograms)

    N = int(np.ceil(totalN * 1.0 / size))
    start, stop = rank * N, min(totalN, (rank + 1) * N)
    print("node %s of %s handles [%s--%s] of %s" % (rank, size, start, stop, totalN))
    if recon is None:
        from .use_tomopy import recon_batch_singlenode as recon

    # progress bar
    # for simplicity, we just report the progress at rank 0, which should be a
    # good indication of progress of all nodes any way
    if rank == 0:
        bar = progressbar.ProgressBar(
            widgets=[
                "Reconstructing",
                progressbar.Percentage(),
                progressbar.Bar(),
                " [",
                progressbar.ETA(),
                "] ",
            ],
            max_value=stop - start,
            **pb_config
        )
    start0 = start  # shall be fine to define inside if-block. Just to make flake8/pylint feel betters

    # avoid infinite loop
    loop = -1

    while start < stop or loop < MAX_LOOP:
        # update loop
        loop += 1

        stop1 = min(start + stepsize, stop)
        logger.debug("node %s of %s working on %s:%s" % (rank, size, start, stop1))
        sinograms1 = sinograms[start:stop1]
        if not len(sinograms1):
            continue
        recon_series1 = recon_series[start:stop1]
        try:
            recon(sinograms1, theta, recon_series1, center=center, **kwds)
        except:
            import traceback as tb

            err = tb.format_exc()
            logger.info("node %s of %s: recon %s:%s failed:\n%s" % (rank, size, start, stop1, err))

        # update range
        start = stop1

        # update bar (rank 0)
        if rank == 0:
            bar.update(start - start0)
        continue
    comm.Barrier()

    if rank == 0:
        print("\n")
    return


# End of file
