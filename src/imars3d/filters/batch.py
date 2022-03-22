# -*- python -*-
# -*- coding: utf-8 -*-

"""
helpers to convert functions working for one image
to functions working for an image series
"""

from __future__ import print_function
import numpy as np, sys, os, time
import progressbar
from imars3d import configuration
pb_config = configuration['progress_bar']

WAIT_COUNT = 10 # wait this many times for the master node to create the output dir
WAIT_SECONDS = 1.0 # wait this many seconds every time

def filter_parallel_onenode(
        ct_series, output_img_series, desc, filter_one, **kwds):
    """
    * ct_series: an image series for ct scan
    * output_img_series: output image series
    * desc: description of the filter action
    * filter_one: function to filter one image
    * kwds: additional kargs for filter_one
    """
    import logging; logger = logging.getLogger("mpi")
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    # start processing at different time
    time.sleep(rank*0.2)
    # create the output dir
    dir = os.path.dirname(output_img_series.filename_template)
    if not os.path.exists(dir):
        if rank == 0:
            os.makedirs(dir)
        else:
            created = False
            for i in range(WAIT_COUNT):
                time.sleep(WAIT_SECONDS)
                if os.path.exists(dir): 
                    created = True
                    break
                continue
            if not created:
                raise IOError("Waited %s seconds, %s still not created" % (
                    WAIT_COUNT*WAIT_SECONDS, dir))
    #
    prefix = "%s %s:" % (desc, ct_series.name or "")
    if rank==0:
        logger.info( "Running %s on %s" % (desc, ct_series.name) )
        pass
    totalN = ct_series.nImages
    # number of images to process in this process
    N = int(np.ceil(totalN*1. / size))
    # start and stop index
    start, stop = rank*N, min(totalN, (rank+1)*N)
    # progress bar
    # for simplicity, we just report the progress at rank 0, which should be a
    # good indication of progress of all nodes any way
    if rank==0:
        bar = progressbar.ProgressBar(
            widgets=[
                prefix,
                progressbar.Percentage(),
                progressbar.Bar(),
                ' [', progressbar.ETA(), '] ',
            ],
            max_value = stop-start-1,
            **pb_config
        )
    for i, angle in enumerate(ct_series.identifiers[start: stop]):
        # sys.stderr.write("%s: %s\n" % (prefix, angle))
        # skip over existing results
        if not output_img_series.exists(angle):
            data = ct_series.getData(angle)
            output_img_series.putImage(angle, filter_one(data, **kwds))
        if rank==0: bar.update(i)
        continue
    comm.Barrier()
    if rank==0: print('\n')
    return
from ..decorators import mpi_parallelize
filter_parallel = mpi_parallelize(filter_parallel_onenode)


def filter(ct_series, output_img_series, desc, filter_one, **kwds):
    """
    * ct_series: an image series for ct scan
    * output_img_series: output image series
    * desc: description of the filter action
    * filter_one: function to filter one image
    * kwds: additional kargs for filter_one
    """
    prefix = "%s %s:" % (desc, ct_series.name or "")
    N = ct_series.nImages
    bar = progressbar.ProgressBar(
        widgets=[
            prefix,
            progressbar.Percentage(),
            progressbar.Bar(),
            ' [', progressbar.ETA(), '] ',
        ],
        max_value = N-1,
        **pb_config
    )
    for i, angle in enumerate(ct_series.identifiers):
        # skip over existing results
        if not output_img_series.exists(angle):
            data = ct_series.getData(angle)
            output_img_series.putImage(angle, filter_one(data, **kwds))
        bar.update(i)
        continue
    print('\n')
    return

# End of file
