# -*- python -*-
# -*- coding: utf-8 -*-


import progressbar

from .AbstractComponent import AbstractComponent


class Projection(AbstractComponent):

    def __call__(self, ct_series, sinograms):
        """convert ct image series to sinogram series"""
        N = ct_series.nImages
        img0 = ct_series[0]
        data0 = img0.data
        Y, X = data0.shape
        # array to hold all data
        import numpy as np
        data = np.zeros( (N, Y, X), dtype="float32")
        # read data
        prefix = "Reading data from %r for sinogram building" % (
            ct_series.name or "",)
        bar = create_pbar(prefix, N-1)
        for i in range(N):
            bar.update(i)
            data[i, :] = ct_series[i].data
            continue
        # 
        prefix = "Computing sinograms from %r" % (ct_series.name or "",)
        bar = create_pbar(prefix, Y-1)
        from ..filters.smoothing import filter_one as smooth
        sinograms.identifiers = range(Y)
        for y in range(Y):
            sino = sinograms[y]
            if sinograms.exists(y):
                print("%s already existed" % sino)
                bar.update(y)
                continue
            sino.data = data[:, y, :]
            sino.data = smooth(sino.data, 3)
            sino.save()
            bar.update(y)
            continue
        return

create_pbar = lambda prefix, max: progressbar.ProgressBar(
    widgets=[
        prefix,
        progressbar.Percentage(),
        progressbar.Bar(),
        ' [', progressbar.ETA(), '] ',
    ],
    max_value = max
)


class Projection_MP(AbstractComponent):

    def __init__(self, num_workers=None):
        self.num_workers = num_workers
        return

    def __call__(self, ct_series, sinograms):
        """convert ct image series to sinogram series"""
        # get metadata for sinograms
        data0 = ct_series[0].data
        Y, X = data0.shape
        sinograms.identifiers = range(Y)
        # call multiprocessing
        import tempfile, pickle, os
        args = ct_series, sinograms
        tmpdir = "_mp_tmp"
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)
        dir = tempfile.mkdtemp(dir=tmpdir)
        # save params
        args_pkl = os.path.join(dir, "args.pkl")
        allargs = args, dict(num_workers=self.num_workers)
        pickle.dump(allargs, open(args_pkl, 'wb'))
        # 
        script = os.path.join(os.path.dirname(__file__), 'projection_mp.py')
        cmd = 'python %s %s' % (script, args_pkl)
        # 
        from ..shutils import exec_withlog
        logfile = os.path.join(dir, 'log.run')
        exec_withlog(cmd, logfile)
        return


# End of file
