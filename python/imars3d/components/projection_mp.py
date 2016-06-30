# -*- python -*-
# -*- coding: utf-8 -*-

import multiprocessing as mp, numpy as np, pickle

# global array
data = None
sinograms_pkl = None

#
def launch_jobs(ct_series, sinograms, num_workers=None):
    global data, sinograms_pkl
    # worker?
    if num_workers is None:
        num_workers = max(mp.cpu_count() - 1, 1)
    N = ct_series.nImages
    img0 = ct_series[0]
    data0 = img0.data
    Y, X = data0.shape
    # update sinograms
    sinograms.identifiers = range(Y)
    # save sinograms (metadata only)
    sinograms_pkl = pickle.dumps(sinograms)
    # array to hold all data
    import numpy as np
    data = np.zeros( (N, Y, X), dtype="float32")
    # read data
    for i in range(N):
        data[i, :] = ct_series[i].data
        continue
    pool = mp.Pool(num_workers)
    return pool.map(job_handler, range(Y))

def job_handler(y):
    sinograms = pickle.loads(sinograms_pkl)
    sino = sinograms[y]
    if sinograms.exists(y):
        print("%s already existed" % sino)
        return y
    sino.data = data[:, y, :]
    from imars3d.filters.smoothing import filter_one as smooth
    sino.data = smooth(sino.data, 5)
    sino.save()
    return y

def main():
    import sys
    args, kwds = pickle.load(open(sys.argv[1]))
    for y in launch_jobs(*args, **kwds):
        continue
    return

if __name__ == '__main__': main()

# End of file
