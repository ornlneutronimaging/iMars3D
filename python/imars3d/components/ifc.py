#!/usr/bin/env python

import numpy as np


def getBG(img, debug=False, **kwds):
    # get boundary
    start_row, stop_row, start_cols, stop_cols = getBoundary(img, **kwds)
    # expand
    NROWS, NCOLS = img.data.shape
    # start_row = max(0, start_row-5)
    # stop_row = min(NROWS-1, stop_row+5)
    start_cols = start_cols // 2
    stop_cols = (stop_cols + NCOLS)//2
    # compute bg
    data = img.data
    left = None; right = None
    for i, row in enumerate(data):
        l = row[:start_cols[i]]
        r = row[stop_cols[i]:]
        if left is None: 
            left = l
        else:
            left = np.concatenate((left, l))
        if right is None:
            right = r
        else:
            right = np.concatenate((right, r))
        continue
    all = np.concatenate((left, right))
    if debug:
        hist, edges = np.histogram(all, bins=np.arange(0.5, 1.5, 0.01))
        c = (edges[1:] + edges[:-1])/2
        from matplotlib import pyplot as plt
        plt.figure()
        plt.plot(c, hist)
        plt.savefig("hist.png")
        plt.close()
    return all.mean()


def getBoundary(img, debug=False, **kwds):
    from skimage import feature
    edge = feature.canny(img.data, **kwds)
    start_row = None
    middle_col = (edge.shape[1]-1)//2
    start_cols = np.ones(edge.shape[0], dtype=int)*middle_col
    stop_cols = np.ones(edge.shape[0], dtype=int)*middle_col
    for i, row in enumerate(edge):
        isedge = row > 0
        if isedge.any():
            w = np.where(isedge)[0]
            start_cols[i], stop_cols[i] = w[0], w[-1]
            # set the row that starts to have object to be measured
            if start_row is None:
                start_row = i
            stop_row = i+1
        continue
    if debug:
        print(start_row, stop_row)
        # for start, stop in zip(start_cols, stop_cols):
        #    print(start, stop)
        #    continue
        from matplotlib import pyplot as plt
        plt.figure()
        plt.plot(start_cols, '.')
        plt.plot(stop_cols, '.')
        plt.savefig("edge.png")
        plt.close()
    return start_row, stop_row, start_cols, stop_cols
