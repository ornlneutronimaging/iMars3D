# -*- python -*-
# -*- coding: utf-8 -*-

"""
helpers to convert functions working for one image
to functions working for an image series
"""

import numpy as np, sys, os, time

def filter_parallel_onenode(
        ct_series, output_img_series, desc, filter_one, **kwds):
    """
    * ct_series: an image series for ct scan
    * output_img_series: output image series
    * desc: description of the filter action
    * filter_one: function to filter one image
    * kwds: additional kargs for filter_one
    """
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    # create the output dir
    dir = os.path.dirname(output_img_series.filename_template)
    if not os.path.exists(dir):
        if rank == 0:
            os.makedirs(dir)
        comm.Barrier()
    # start processing at different time
    time.sleep(rank*0.2)
    #
    prefix = "%s %s:" % (desc, ct_series.name or "")
    totalN = ct_series.nImages
    # number of images to process in this process
    N = int(np.ceil(totalN*1. / size))
    # start and stop index
    start, stop = rank*N, min(totalN, (rank+1)*N)
    # 
    for angle in ct_series.identifiers[start: stop]:
        print>>sys.stderr, "%s: %s" % (prefix, angle)
        # skip over existing results
        if not output_img_series.exists(angle):
            data = ct_series.getData(angle)
            output_img_series.putImage(angle, filter_one(data, **kwds))
        continue
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
    import progressbar
    bar = progressbar.ProgressBar(
        widgets=[
            prefix,
            progressbar.Percentage(),
            progressbar.Bar(),
            ' [', progressbar.ETA(), '] ',
        ],
        max_value = N-1
    )
    for i, angle in enumerate(ct_series.identifiers):
        # skip over existing results
        if not output_img_series.exists(angle):
            data = ct_series.getData(angle)
            output_img_series.putImage(angle, filter_one(data, **kwds))
        bar.update(i)
        continue
    print
    return

# End of file
